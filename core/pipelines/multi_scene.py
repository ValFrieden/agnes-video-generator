"""core.pipelines.multi_scene — 多场景视频通用框架（v4.0 重构核心）

模板方法 ``run()`` 定义标准流程：
    build_scenes → build_reference_images → generate_videos → audio+subtitle → composite

子类只需提供数据来源（_build_scenes / _build_reference_images / _composite_final），
并可按需覆写通用步骤（_generate_videos / _generate_audio / _generate_subtitles）或钩子方法。

设计原则（见 docs/plans/v4.0/pipeline_refactor.md）：
    - 差异只在"数据从哪来"，不在"流程怎么做"
    - 通用步骤操作 ``self._state.scenes: List[SceneTask]``，通过钩子读取每场景参数
    - 子类可整体覆写某步骤以保留其特有的（如链式/循环）视频生成逻辑
"""

import asyncio
import logging
import os
import traceback
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional

from core.api.agnes_video import VideoTaskCancelled, is_remote_video_failure
from core.compositor.processor import VideoProcessor
from core.pipelines import BasePipeline, CheckpointPause, PipelineShutdown
from models.task import SceneTask, StepStatus
from utils.network import (
    describe_network_error,
    describe_queue_full_error,
    queue_full_message_params,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 命名常量（v5.0 Batch 5 / 5.3 魔法数字收敛）
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class StepProgressLimits:
    """模板方法各阶段的进度边界（0.0 ~ 1.0）。"""

    build_start: float = 0.0      # Phase 1 分镜
    build_end: float = 0.15
    reference_end: float = 0.30   # Phase 2 参考图
    keyframe_end: float = 0.40    # Phase 2.5 关键帧（v7.1，仅 generate_keyframes 时经过）
    video_end: float = 0.75       # Phase 3 视频生成
    qc_end: float = 0.80          # Phase 3.5 VLM 质量闸（v7.2 R8，仅 qc_enabled 时经过）
    audio_end: float = 0.85       # Phase 4 配音
    subtitle_end: float = 0.90    # Phase 5 字幕
    composite_end: float = 0.98   # Phase 6 合成
    done: float = 1.0             # 完成


_PROGRESS = StepProgressLimits()

# 失败/中断事件的统一进度值
_PROGRESS_FAILED = 0.0

# 视频等待失败的重试间隔基数（秒）：delay = 基数 * (retry + 1)
_RETRY_INTERVAL_BASE_SECONDS = 20


class MultiScenePipeline(BasePipeline):
    """多场景视频生成通用框架。

    提供统一的步骤编排（模板方法 ``run``）、步骤执行包装器（``_execute_step``）、
    通用水印后处理（继承自 ``BasePipeline``）、以及通用视频/音频/字幕生成实现。

    子类必须实现三个抽象方法提供数据源：
        - ``_build_scenes``         构建 ``self._state.scenes``（List[SceneTask]）
        - ``_build_reference_images`` 生成参考图（可空实现跳过）
        - ``_composite_final``      合成最终视频

    并可通过钩子方法定制参数来源：
        - ``_get_narration_text``        配音文本
        - ``_get_segment_texts_and_durations`` 字幕分段文本与时长
        - ``_get_scene_video_prompt``     单场景视频 prompt
        - ``_get_scene_ref_images``       单场景参考图列表
        - ``_get_scene_duration``         单场景视频时长
        - ``_get_audio_path``             音频文件输出路径
        - ``_set_subtitle_paths``         字幕路径写回 state

    v7.1 关键帧模式：开启 ``state.generate_keyframes`` 的子类须在 ``__init__``
    中设置 ``self.image_api``（``AgnesImageAPI`` 实例），供
    ``_generate_scene_keyframes`` 生成关键帧静图使用。
    """

    # v5.0 Batch 3（S3，方案 A）：粗粒度步骤级 skip 默认开启；
    # Creative 依赖各 ``_step_*`` 读盘做细粒度续传，置 False 禁用（原覆写已删除）。
    coarse_skip: bool = True

    # ==================================================================
    # 模板方法：run()
    # ==================================================================

    async def run(self, state) -> str:
        """标准多场景视频流程（模板方法）。"""
        self._state = state
        self._state.status = StepStatus.RUNNING
        self.task_manager.create(self._state)

        await self._emit("init", "running", self._get_init_message(), _PROGRESS.build_start)

        try:
            # Phase 1: 分镜/拆段 → List[SceneTask]
            await self._execute_step(
                "step_build_scenes", self._build_scenes,
                _PROGRESS.build_start, _PROGRESS.build_end,
                self._t("progress.multi_scene.scenes_running"), self._t("progress.multi_scene.scenes_done"),
            )

            # Phase 2: 参考图（可选，子类可空实现跳过）
            await self._execute_step(
                "step_reference_images", self._build_reference_images,
                _PROGRESS.build_end, _PROGRESS.reference_end,
                self._t("progress.multi_scene.reference_running"), self._t("progress.multi_scene.reference_done"),
            )

            # Phase 2.5（v7.1 关键帧模式，I2V-first）：逐场景先生成关键帧静图。
            # 关闭时不执行该步骤（step_keyframes 保持 PENDING，前端按
            # state.generate_keyframes 过滤时间线，不显示该步骤）。
            if self._keyframes_enabled():
                await self._execute_step(
                    "step_keyframes", self._generate_scene_keyframes,
                    _PROGRESS.reference_end, _PROGRESS.keyframe_end,
                    self._t("progress.multi_scene.keyframes_running"),
                    self._t("progress.multi_scene.keyframes_done"),
                )

            # Phase 3: 视频生成（通用，子类可覆写保留链式/循环逻辑）
            # 收尾时为每个成片补一张 25/50/75% 接触单（铁律「单段确认」的人工可审依据）；
            # 复用视频步骤的进度区间，不引入新步骤字段，失败一律 fail-open。
            await self._execute_step(
                "step_video_generation", self._generate_videos_with_contact_sheets,
                _PROGRESS.keyframe_end, _PROGRESS.video_end,
                self._t("progress.multi_scene.videos_running"), self._t("progress.multi_scene.videos_done"),
            )

            # Phase 3.5（v7.2 R8 质量闸，opt-in）：逐场景免费 VLM 检查 + FAIL 自动
            # 重生成一次。关闭时不执行（step_qc 保持 PENDING，前端按
            # state.qc_enabled 过滤时间线，与 keyframes 步骤同模式）。
            if self._qc_enabled():
                await self._execute_step(
                    "step_qc", self._run_scene_qc,
                    _PROGRESS.video_end, _PROGRESS.qc_end,
                    self._t("progress.multi_scene.qc_running"),
                    self._t("progress.multi_scene.qc_done"),
                )

            # Phase 4: 配音（通用，子类可覆写）
            sub_maker = await self._execute_step(
                "step_audio", self._generate_audio,
                _PROGRESS.video_end, _PROGRESS.audio_end,
                self._t("progress.multi_scene.audio_running"), self._t("progress.multi_scene.audio_done"),
            )

            # Phase 5: 字幕（通用，子类可覆写）
            await self._execute_step(
                "step_subtitle",
                lambda: self._generate_subtitles(sub_maker),
                _PROGRESS.audio_end, _PROGRESS.subtitle_end,
                self._t("progress.multi_scene.subtitles_running"), self._t("progress.multi_scene.subtitles_done"),
            )

            # Phase 6: 合成
            final_video = await self._execute_step(
                "step_concatenation", self._composite_final,
                _PROGRESS.subtitle_end, _PROGRESS.composite_end,
                self._t("progress.multi_scene.composite_running"), self._t("progress.multi_scene.composite_done"),
            )

            # 后处理：可选 3D LUT 调色 + 水印（异步，避免阻塞事件循环）
            final_video = await self._apply_lut(final_video)
            final_video = await self._apply_watermark(final_video)

            # Post-Processing (AGNES_POST_PROCESS=1 aktiviert auto-editor Stille-Entfernung im ThreadPool)
            from core.compositor.post_processor import post_process_video_async
            final_video = await post_process_video_async(final_video)  # in-place, graceful degradation bei Fehler

            # 完成
            self._state.status = StepStatus.COMPLETED
            self._state.final_video_file = final_video
            self.task_manager.update_state(
                status=StepStatus.COMPLETED,
                final_video_file=final_video,
            )
            await self._emit(
                "done", "completed", self._t("progress.multi_scene.done"), _PROGRESS.done,
                {"final_video": final_video},
            )
            return final_video

        except CheckpointPause as e:
            # 手动模式暂停：状态已在 _maybe_pause 落盘为 PENDING + current_checkpoint，
            # 这里正常返回（非失败、非中断），等待用户确认后 resume 继续。
            logger.info("[MultiScene] Task %s paused: %s", self.task_id, e.message)
            return ""
        except PipelineShutdown:
            self._mark_interrupted()
            # v7.0（issue #64）：中断提示按任务落盘的 ui_language 双语化
            await self._emit(
                "error", "failed", self._t("task.interrupted_resumable"),
                _PROGRESS_FAILED,
                preserve_step=True,
            )
            raise
        except Exception as e:
            # 网络 / 域名解析类故障翻译成可自助排查的提示（issue #56/#57：此前只抛
            # RetryError[...]，用户看不出是本机 DNS 问题，反复点「重试任务」无效）
            # v7.0（issue #64）：按 state.ui_language 输出中/英文，避免英文界面看到中文诊断
            # v7.0 U1：队列满优先走结构化提示（前端按 22 语言渲染，后端给 zh/en 兜底）
            message = (
                describe_queue_full_error(e, lang=self._ui_lang())
                or describe_network_error(e, lang=self._ui_lang())
                or str(e)
            )
            message_key = "error.video.queue_full" if queue_full_message_params(e) else None
            message_params = queue_full_message_params(e) or None
            failed_step = self._state.current_step if self._state else ""
            # 持久化完整 traceback，供诊断端点/前端反馈报告暴露（定位环境级异常如 [WinError 2]）
            self._state.status = StepStatus.FAILED
            self.task_manager.update_state(
                status=StepStatus.FAILED,
                error_traceback=traceback.format_exc(),
                # 失败即落盘真实环节 + 可读消息：诊断报告的「失败环节」不再依赖前端
                # 挂载时的快照，也不会因进度写盘节流而停留在很久以前的旧值
                current_step=failed_step,
                current_status="failed",
                current_message=message,
            )
            logger.error(
                "[MultiScene] Task %s failed at step '%s': %s",
                self.task_id, failed_step, e,
            )
            await self._emit(
                "error", "failed", message, _PROGRESS_FAILED, preserve_step=True,
                message_key=message_key, message_params=message_params,
            )
            raise

    # ==================================================================
    # 步骤执行包装器
    # ==================================================================

    async def _execute_step(
        self, step_name: str, action: Callable,
        progress_start: float, progress_end: float,
        running_msg: str, completed_msg: str,
        coarse_skip: Optional[bool] = None,
    ):
        """统一的步骤执行器：自动处理断点续传、状态标记、进度上报。

        断点续传规则：启用粗粒度 skip 时（显式 ``coarse_skip`` 覆盖，缺省取
        ``self.coarse_skip``），若 ``self._state`` 上对应步骤字段已为 COMPLETED
        则整步跳过；禁用时总是执行，由步骤内部按文件/字段做细粒度续传。
        """
        skip_enabled = self.coarse_skip if coarse_skip is None else coarse_skip
        if skip_enabled and getattr(self._state, step_name, StepStatus.PENDING) == StepStatus.COMPLETED:
            logger.info(f"[Pipeline] Step {step_name}: already completed, skipping")
            return None

        self.task_manager.update_step(step_name, StepStatus.RUNNING)
        await self._emit(step_name, "running", running_msg, progress_start)

        result = await action()

        self.task_manager.update_step(step_name, StepStatus.COMPLETED)
        await self._emit(step_name, "completed", completed_msg, progress_end)

        # v6.0 手动模式：步骤完成后检查是否命中暂停点（coarse_skip 跳过的不触发）。
        # 传入步骤完成进度，暂停点展示真实进度而非 100%。
        await self._maybe_pause(step_name, progress_end)
        return result

    # ==================================================================
    # 抽象方法：数据来源（子类必须实现）
    # ==================================================================

    @abstractmethod
    async def _build_scenes(self) -> None:
        """构建场景列表，产出 ``self._state.scenes``（List[SceneTask]）。"""
        ...

    @abstractmethod
    async def _build_reference_images(self) -> None:
        """构建参考图。可空实现（直接 ``return``）跳过此阶段。"""
        ...

    @abstractmethod
    async def _composite_final(self) -> str:
        """合成最终视频，返回视频路径。"""
        ...

    # ==================================================================
    # 通用步骤实现（操作 self._state.scenes，子类可整体覆写）
    # ==================================================================

    async def _generate_videos_with_contact_sheets(self) -> None:
        """视频生成 + 逐片段 25/50/75% 接触单（QC-Trio）。

        接触单是铁律「单段确认流程」的可审依据：VLM 闸（``_run_scene_qc``，opt-in）
        自动判定，接触单让人能一眼看到片段的开始/中段/结尾三帧。生成失败一律
        fail-open——质检辅助物绝不能拖垮任务本身。
        """
        try:
            await self._generate_videos()
        finally:
            self._write_all_contact_sheets()

    def _write_all_contact_sheets(self) -> None:
        """为所有已落盘的成片补接触单（已存在则跳过，纯新增文件）。"""
        from core.quality.qc import build_contact_sheet

        scenes = getattr(self._state, "scenes", None) or []
        for idx, scene in enumerate(scenes):
            video_path = getattr(scene, "video_file", None)
            if not video_path or not os.path.isfile(video_path):
                continue
            target = os.path.join(os.path.dirname(video_path), "qa_trio.png")
            if os.path.isfile(target):
                continue
            try:
                made = build_contact_sheet(video_path, out_path=target)
            except Exception as e:  # noqa: BLE001 — fail-open by design
                logger.warning("[MultiScene] contact sheet failed for scene %d: %s", idx + 1, e)
                continue
            if made:
                logger.info("[MultiScene] contact sheet (25/50/75%%) ready for scene %d: %s", idx + 1, made)

    async def _generate_videos(self) -> None:
        """通用视频生成：两阶段（批量提交 + 逐个等待）。

        每个场景从 SceneTask 对象获取 prompt / duration / ref_images（通过钩子）。
        子类（如链式/循环视频）可整体覆写本方法以保留其特有逻辑。

        v7.1.2：``AGNES_SCENE_FRAME_CHAINING=1`` 时改走串行首末帧链
        （``_generate_videos_chained``）；关键帧模式自带 i2i 视觉链，不叠加，
        仍走本通用路径。
        """
        if self._frame_chaining_enabled():
            logger.info(
                "[MultiScene] frame chaining enabled (AGNES_SCENE_FRAME_CHAINING): "
                "using serial last→first frame generation"
            )
            return await self._generate_videos_chained()

        scenes = self._state.scenes

        # v7.2 R8（P2）：成本估算 + 预算闸 —— 付费 Provider 在第一次提交前 fail-fast
        await self._announce_video_cost(self._remaining_submit_indices(len(scenes)))

        # Phase 1: 批量提交
        pending: list = []
        for i, scene in enumerate(scenes):
            self._check_shutdown()
            scene_dir = os.path.join(self.working_dir, f"scene_{i}")
            os.makedirs(scene_dir, exist_ok=True)
            video_path = os.path.join(scene_dir, "video.mp4")

            if os.path.exists(video_path):
                scene.video_file = video_path
                continue

            video_id = self._load_task_json(scene_dir)
            if video_id:
                scene.video_id = video_id
                pending.append((i, video_id, video_path))
                continue

            prompt = self._get_scene_video_prompt(scene, i)
            ref_images = self._get_scene_ref_images(scene, i)
            await self._guard_scene_reference(scene, i, ref_images)
            duration = self._get_scene_duration(scene, i)

            video_id = await self.video_api.submit_video(
                prompt=prompt,
                reference_image_paths=ref_images,
                duration=duration,
                width=self._state.video_width,
                height=self._state.video_height,
                # U1（v7.0）：队列满时实时向前端推「排队重试中」
                progress_callback=self._submit_progress_callback("video_gen", 0.40),
            )
            scene.video_id = video_id
            self._save_task_json(scene_dir, {"video_id": video_id})
            pending.append((i, video_id, video_path))

        self.task_manager.update_state(scenes=[s.model_dump() for s in scenes])

        # Phase 2: 并发等待全部视频（优化路线图 1.3）
        # 此前逐场景串行 wait_for_video，N 场景等待时长线性叠加；改为并行轮询
        # （视频 API 本身异步），整体耗时 ≈ 最慢场景，随后逐个落盘并上报进度。
        if pending:
            await self._emit(
                "video_gen", "running",
                self._t("progress.multi_scene.wait_videos", n=len(pending)),
                0.40,
            )

        async def _wait_one(idx: int, vid: str):
            out = await self._wait_for_video_with_retry(vid, idx)
            return idx, out

        done = await asyncio.gather(
            *[_wait_one(i, vid) for i, vid, _ in pending],
            return_exceptions=True,
        )
        # 任一场景失败 / 停止：立即穿透（保持 0.2 的停止即时性与异常语义）
        for item in done:
            if isinstance(item, BaseException):
                raise item
        results = dict(done)

        # 逐个落盘 + 上报进度（保存为磁盘 IO，串行避免并发写）
        for j, (scene_idx, video_id, video_path) in enumerate(pending):
            self._check_shutdown()
            video_output = results[scene_idx]
            await video_output.save(video_path)
            self._state.scenes[scene_idx].video_file = video_path
            self.task_manager.update_state(scenes=[s.model_dump() for s in self._state.scenes])
            await self._emit(
                "video_gen", "running",
                self._t("progress.multi_scene.save_video", cur=j + 1, total=len(pending)),
                0.40 + 0.35 * (j + 1) / max(len(pending), 1),
            )

    # ==================================================================
    # v7.2 R8（P2）：成本估算 + 预算闸（仅付费 Provider 生效，agnes 无估算器直接跳过）
    # ==================================================================

    def _remaining_submit_indices(self, total: int) -> List[int]:
        """将被**新提交**的场景下标（已有成片或已排队 task.json 的不计费）。"""
        out: List[int] = []
        for i in range(total):
            scene_dir = os.path.join(self.working_dir, f"scene_{i}")
            if os.path.exists(os.path.join(scene_dir, "video.mp4")):
                continue
            if self._load_task_json(scene_dir):
                continue
            out.append(i)
        return out

    async def _announce_video_cost(self, submit_indices: List[int]) -> None:
        """视频生成前估算剩余成本、落盘并做预算预检。

        - ``video_api`` 无 ``estimate_clip_cost_usd``（agnes 免费）→ 直接返回；
        - 付费 Provider：估算写 ``state.estimated_video_cost_usd``，并经结构化
          进度消息（``progress.multi_scene.cost_estimate``）下发前端；
        - ``AGNES_VIDEO_BUDGET_USD > 0`` 且估算超限 → 在产生任何费用**之前**
          抛 RuntimeError（走 run() 的统一失败路径，消息含预算与金额）。
        """
        if not submit_indices:
            return
        estimator = getattr(self.video_api, "estimate_clip_cost_usd", None)
        if not callable(estimator):
            return
        total = 0.0
        try:
            for i in submit_indices:
                result = estimator(
                    self._get_scene_duration(self._state.scenes[i], i),
                    self._state.video_width,
                    self._state.video_height,
                )
                # Mocks/async-Provider können eine Coroutine liefern
                if asyncio.iscoroutine(result):
                    result = await result
                total += float(result or 0)
        except Exception as e:
            # Kostenschätzung ist Best-Effort: Fehler nie zum Task-Fehler machen
            logger.warning("[MultiScene] cost estimate failed (ignored): %s", e)
            return
        if total <= 0:
            return
        self.task_manager.update_state(estimated_video_cost_usd=total)
        from core.config import get_settings

        budget = float(get_settings().agnes_video_budget_usd or 0.0)
        if budget > 0 and total > budget:
            raise RuntimeError(self._t(
                "error.video.budget_exceeded",
                cost=f"{total:.2f}", budget=f"{budget:.2f}",
            ))
        await self._emit(
            "video_gen", "running",
            self._t("progress.multi_scene.cost_estimate", cost=f"{total:.2f}"),
            0.40,
            message_key="progress.multi_scene.cost_estimate",
            message_params={"cost": f"{total:.2f}"},
        )

    # ==================================================================
    # v7.2 R8（Batch 2）：VLM 质量闸（opt-in，state.qc_enabled）
    # 免费 Agnes-Vision 逐场景检查；FAIL 自动重生成一次，仍 FAIL 保留原片 +
    # qc_report 标记人工复核。fail-open：QC 自身故障绝不拖垮任务。
    # ==================================================================

    # 每个片段的最大重生成轮数（1 = 首检 FAIL 后重生成一次，与实验闸一致）
    _QC_MAX_REGEN_ROUNDS = 1

    def _qc_enabled(self) -> bool:
        """质量闸是否开启（state.qc_enabled，旧任务缺字段视为关闭）。"""
        return bool(getattr(self._state, "qc_enabled", False))

    def _get_qc_gate(self):
        """构建 ClipQCGate（AgnesChatAPI 调用时导入 — mock 回归补丁点）。"""
        from core.api.agnes_chat import AgnesChatAPI
        from core.quality.qc import ClipQCGate

        return ClipQCGate(AgnesChatAPI(api_key=self.api_key))

    # ── 子类可覆写的钩子 ─────────────────────────────────────────

    def _scene_clip_path(self, scene: SceneTask, index: int) -> str:
        """场景成片路径（默认 ``scene_{i}/video.mp4``；稿件覆写为 para 目录）。"""
        return os.path.join(self.working_dir, f"scene_{index}", "video.mp4")

    def _qc_scene_dir(self, scene: SceneTask, index: int) -> str:
        """该片段 task.json 所在目录（重生成前清空排队 id 用）。"""
        return os.path.join(self.working_dir, f"scene_{index}")

    def _qc_clip_prompt(self, scene: SceneTask, index: int) -> str:
        """QC 判定依据的 prompt（默认与视频提交 prompt 同源）。"""
        return self._get_scene_video_prompt(scene, index)

    def _qc_regen_refs(self, scene: SceneTask, index: int) -> List[str]:
        """重生成时的参考图（默认与通用提交路径同源）。"""
        return self._get_scene_ref_images(scene, index)

    def _qc_regen_duration(self, scene: SceneTask, index: int) -> int:
        """重生成的片段时长（默认与通用提交路径同源）。"""
        return self._get_scene_duration(scene, index)

    # ── 主流程 ───────────────────────────────────────────────────

    async def _run_scene_qc(self) -> None:
        """逐场景 VLM 质量检查 + 有限自动重生成（Phase 3.5）。

        - 检查所有已成片场景（``_scene_clip_path``）；
        - 结论写 ``state.qc_report``（逐场景 passed/verdict）并落盘；
        - FAIL 场景：清空排队 task.json → 原样重新提交（重生成计入付费
          Provider 的预算闸）→ 等待落盘 → 复检；复检仍 FAIL 保留新片并标记；
        - 原片在重生成功落盘前**始终保留**（重生成等待失败不丢已有产物）。
        """
        scenes = self._state.scenes
        total = len(scenes)
        gate = self._get_qc_gate()
        fixed = 0
        flagged = 0

        for i, scene in enumerate(scenes):
            self._check_shutdown()
            clip_path = self._scene_clip_path(scene, i)
            if not clip_path or not os.path.exists(clip_path):
                continue

            await self._emit(
                "qc", "running",
                self._t("progress.multi_scene.qc_scene", i=i + 1, total=total),
                _PROGRESS.video_end + (_PROGRESS.qc_end - _PROGRESS.video_end)
                * (i / max(total, 1)),
            )

            verdict = await gate.judge_clip(clip_path, self._qc_clip_prompt(scene, i))
            self._record_qc_verdict(i, verdict)

            if not verdict.passed:
                logger.warning(
                    "[MultiScene] qc: clip %d FAIL → regenerating (%s)",
                    i, verdict.reason[:160],
                )
                regen_verdict = await self._qc_regenerate_clip(i, gate)
                if not regen_verdict.passed:
                    flagged += 1
                    logger.warning(
                        "[MultiScene] qc: clip %d still FAIL after regen "
                        "(kept for manual review): %s",
                        i, regen_verdict.reason[:160],
                    )
                else:
                    fixed += 1

        self.task_manager.update_state(qc_report=self._state.qc_report)
        await self._emit(
            "qc", "completed",
            self._t(
                "progress.multi_scene.qc_done",
                total=total, fixed=fixed, flagged=flagged,
            ),
            _PROGRESS.qc_end,
            message_key="progress.multi_scene.qc_done",
            message_params={"total": total, "fixed": fixed, "flagged": flagged},
        )

    def _record_qc_verdict(self, index: int, verdict) -> None:
        """单场景 QC 结论写 state + 落盘（供前端/诊断展示）。"""
        self._state.qc_report[str(index)] = {
            "passed": bool(verdict.passed),
            "verdict": verdict.reason[:300],
        }
        self.task_manager.update_state(qc_report=self._state.qc_report)

    async def _qc_regenerate_clip(self, index: int, gate):
        """重生成 FAIL 片段并复检；任何失败都 fail-open（返回 PASS 型结论语义的
        「无法处理」由调用方按仍 FAIL 处理——此处直接回传复检结论或 fail-open）。"""
        scene = self._state.scenes[index]
        scene_dir = self._qc_scene_dir(scene, index)
        clip_path = self._scene_clip_path(scene, index)

        task_file = os.path.join(scene_dir, "task.json")
        if os.path.exists(task_file):
            os.remove(task_file)

        try:
            video_id = await self.video_api.submit_video(
                prompt=self._qc_clip_prompt(scene, index),
                reference_image_paths=self._qc_regen_refs(scene, index),
                duration=self._qc_regen_duration(scene, index),
                width=self._state.video_width,
                height=self._state.video_height,
                progress_callback=self._submit_progress_callback("qc", _PROGRESS.video_end),
            )
            self._save_task_json(scene_dir, {"video_id": video_id})
            video_output = await self._wait_for_video_with_retry(video_id, index)
            await video_output.save(clip_path)
        except VideoTaskCancelled:
            raise
        except Exception as e:
            # 重生成失败：保留原片，结论按仍 FAIL 记录（人工复核）
            logger.warning("[MultiScene] qc regen clip %d failed: %s", index, e)
            from core.quality.qc import QCVerdict

            fail = QCVerdict(passed=False, reason=f"regen failed (original kept): {e}")
            self._record_qc_verdict(index, fail)
            return fail

        regen_verdict = await gate.judge_clip(
            clip_path, self._qc_clip_prompt(scene, index),
        )
        self._record_qc_verdict(index, regen_verdict)
        return regen_verdict

    # ==================================================================
    # v7.1.2 首末帧链式生成（AGNES_SCENE_FRAME_CHAINING=1，默认关闭）
    # ==================================================================

    def _frame_chaining_enabled(self) -> bool:
        """首末帧链式生成开关。

        env ``AGNES_SCENE_FRAME_CHAINING``（默认关闭，维护模式保守默认）；
        关键帧模式（I2V-first）已在关键帧层实现 i2i 视觉链，不叠加，恒为 False。
        """
        if self._keyframes_enabled():
            return False
        from core.config import get_settings
        return bool(get_settings().agnes_scene_frame_chaining)

    async def _extract_scene_last_frame(self, video_path: str, scene_dir: str) -> str:
        """提取场景成片最后一帧作为下一场景的首帧参考。

        结果缓存为 ``scene_{i}/last_frame.png``（续传直接复用）；
        提取失败返回空串（fail-open：链条断开但任务继续）。
        """
        frame_path = os.path.join(scene_dir, "last_frame.png")
        if os.path.exists(frame_path):
            return frame_path
        try:
            return await asyncio.to_thread(
                VideoProcessor.extract_last_frame, video_path, frame_path,
            )
        except Exception as e:
            logger.warning(
                "[MultiScene] extract last frame failed for %s: %s", video_path, e,
            )
            return ""

    async def _generate_videos_chained(self) -> None:
        """串行首末帧链式视频生成（Last-Frame → First-Frame）。

        知识库调研（watch KB #120/#188，Seedance/Veo 实践）验证的接景技法：
        上一场景成片的最后一帧作为下一场景的首帧参考（单参考 → v2.0
        ``ti2vid`` 首帧初始化 / 2.5 ``reference`` 模式），消除场景间视觉跳变。

        语义约束：
        - 串行依赖：场景 i+1 的提交在场景 i 成片之后，总耗时 ≈ 各场景之和
          （放弃通用路径的并发等待优化，换取场景间连续性）。
        - 链式参考只在场景自身无参考图时叠加：与用户参考图混用会触发
          keyframes/reference 多图模式，首帧语义不可控（v2.0 keyframes 取
          refs[0]/refs[-1] 为首末帧）。
        - 断点续传与通用路径同规则：``video.mp4`` 已在 → 跳过生成、仅提取
          末帧延续链条；``task.json`` 有 video_id → 等待成片，不重复提交。
        - 末帧提取失败 → 该处链条断开，下一场景退回 text-to-video。
        """
        scenes = self._state.scenes
        total = len(scenes)
        prev_last_frame = ""

        # v7.2 R8（P2）：链式路径同样在提交前做成本估算 + 预算闸
        await self._announce_video_cost(self._remaining_submit_indices(total))

        await self._emit(
            "video_gen", "running",
            self._t("progress.multi_scene.wait_videos", n=total),
            0.40,
        )

        for i in range(total):
            self._check_shutdown()
            # 注意：update_state(scenes=...) 会以 model_dump 重建 scenes 列表，
            # 禁止跨 update_state 持有旧 SceneTask 引用——每轮从
            # self._state.scenes 重新取对象，写回也一律走 self._state.scenes[i]
            scene = self._state.scenes[i]
            scene_dir = os.path.join(self.working_dir, f"scene_{i}")
            os.makedirs(scene_dir, exist_ok=True)
            video_path = os.path.join(scene_dir, "video.mp4")

            if os.path.exists(video_path):
                scene.video_file = video_path
                prev_last_frame = await self._extract_scene_last_frame(video_path, scene_dir)
                await self._emit(
                    "video_gen", "running",
                    self._t("progress.multi_scene.save_video", cur=i + 1, total=total),
                    0.40 + 0.35 * (i + 1) / max(total, 1),
                )
                continue

            video_id = self._load_task_json(scene_dir)
            if not video_id:
                prompt = self._get_scene_video_prompt(scene, i)
                ref_images = self._get_scene_ref_images(scene, i)
                duration = self._get_scene_duration(scene, i)
                # 链式首帧：仅当场景无自身参考图时叠加（见方法 docstring 语义约束）
                refs = list(ref_images)
                if prev_last_frame and not refs:
                    refs = [prev_last_frame]
                # 校验放在链式叠加之后：上一段尾帧也算有效参考图
                await self._guard_scene_reference(scene, i, refs)
                video_id = await self.video_api.submit_video(
                    prompt=prompt,
                    reference_image_paths=refs,
                    duration=duration,
                    width=self._state.video_width,
                    height=self._state.video_height,
                    # U1（v7.0）：队列满时实时向前端推「排队重试中」
                    progress_callback=self._submit_progress_callback("video_gen", 0.40),
                )
                scene.video_id = video_id
                self._save_task_json(scene_dir, {"video_id": video_id})

            video_output = await self._wait_for_video_with_retry(video_id, i)
            await video_output.save(video_path)
            self._state.scenes[i].video_file = video_path
            self.task_manager.update_state(
                scenes=[s.model_dump() for s in self._state.scenes],
            )
            prev_last_frame = await self._extract_scene_last_frame(video_path, scene_dir)
            await self._emit(
                "video_gen", "running",
                self._t("progress.multi_scene.save_video", cur=i + 1, total=total),
                0.40 + 0.35 * (i + 1) / max(total, 1),
            )

    # ==================================================================
    # v7.1 关键帧模式（I2V-first）：逐场景先出关键帧静图，再以 i2v 提交动画
    # ==================================================================

    def _keyframes_enabled(self) -> bool:
        """关键帧模式是否开启（state.generate_keyframes，旧任务缺字段视为关闭）。"""
        return bool(getattr(self._state, "generate_keyframes", False))

    async def _generate_scene_keyframes(self) -> None:
        """通用关键帧生成：逐场景出首帧静图（断点续传：已存在的帧跳过）。

        链式一致性：场景 i 的关键帧默认以场景 i-1 的关键帧做 i2i 参考
        （视觉链，对齐 creative 尾帧链做法）；首场景无参考走 t2i。
        子类可通过钩子定制 prompt / 参考优先级 / 落盘目录 / 状态持久化。
        """
        scenes = self._state.scenes
        total = len(scenes)
        size = f"{self._state.video_width}x{self._state.video_height}"
        prev_keyframe = ""

        for i, scene in enumerate(scenes):
            self._check_shutdown()

            # 断点续传：帧已存在（文件在且路径已登记）→ 跳过生成，仅延续视觉链
            existing = getattr(scene, "keyframe_file", "")
            if existing and os.path.exists(existing):
                prev_keyframe = existing
                continue

            rel_dir = self._keyframe_rel_dir(scene, i)
            scene_dir = os.path.join(self.working_dir, rel_dir)
            os.makedirs(scene_dir, exist_ok=True)
            kf_path = os.path.join(scene_dir, "keyframe.png")

            await self._emit(
                "keyframes", "running",
                self._t("progress.multi_scene.keyframe_scene", i=i + 1, total=total),
                _PROGRESS.reference_end + (_PROGRESS.keyframe_end - _PROGRESS.reference_end) * (i + 1) / max(total, 1),
            )

            prompt = self._get_scene_keyframe_prompt(scene, i)
            refs = self._get_scene_keyframe_refs(scene, i, prev_keyframe)
            img_output = await self.image_api.generate_single_image(
                prompt=prompt,
                reference_image_paths=refs,
                size=size,
            )
            await img_output.save(kf_path)

            scene.keyframe_file = kf_path
            prev_keyframe = kf_path
            self._persist_keyframe_state(i)
            logger.info(
                "[MultiScene] keyframe: scene %d/%d saved → %s (refs=%d)",
                i + 1, total, kf_path, len(refs),
            )

    def _get_scene_keyframe_prompt(self, scene: SceneTask, index: int) -> str:
        """关键帧 prompt。默认复用场景视频 prompt（其中已含风格描述）。"""
        return getattr(scene, "scene_prompt", "") or getattr(scene, "end_frame_prompt", "")

    def _get_scene_keyframe_refs(
        self, scene: SceneTask, index: int, prev_keyframe: str,
    ) -> List[str]:
        """关键帧 i2i 参考。默认上一场景关键帧（视觉链）；首场景空（t2i）。"""
        return [prev_keyframe] if prev_keyframe else []

    def _keyframe_rel_dir(self, scene: SceneTask, index: int) -> str:
        """关键帧落盘子目录。默认 ``scene_{i}``（子类如稿件覆写为 ``para_{index}``）。"""
        return f"scene_{index}"

    def _persist_keyframe_state(self, last_index: int) -> None:
        """单个关键帧落盘后的状态持久化。默认回写 scenes 列表。"""
        self.task_manager.update_state(
            scenes=[s.model_dump() for s in self._state.scenes],
        )

    async def _wait_for_video_with_retry(
        self, video_id: str, scene_idx: int, max_retries: int = 3
    ):
        """带重试的视频等待。

        优化路线图 0.2：
        1. 用户停止（``VideoTaskCancelled``）不再被当作可重试的临时错误，直接
           穿透——此前停止会走 20s/40s 退避重试，导致「点停止后最长 ~120s 才停」。
        2. ``task.json`` 仅在**确认服务端失败**时删除；超时、用户取消、网络中断
           一律保留，否则续传只能重新提交，浪费 1 次/分钟/Key 的视频配额。
        """
        scene_dir = os.path.join(self.working_dir, f"scene_{scene_idx}")
        for retry in range(max_retries):
            try:
                return await self.video_api.wait_for_video(video_id)
            except VideoTaskCancelled:
                # 用户停止：不重试、不删 task.json，立即穿透
                raise
            except Exception as e:
                if retry < max_retries - 1:
                    delay = _RETRY_INTERVAL_BASE_SECONDS * (retry + 1)
                    logger.warning(
                        f"Video {video_id[:16]} retry {retry + 1}/{max_retries}: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    if is_remote_video_failure(e):
                        tf = os.path.join(scene_dir, "task.json")
                        if os.path.exists(tf):
                            os.remove(tf)
                    raise

    async def _generate_audio(self) -> Optional[object]:
        """通用 TTS 音频生成（EdgeTTS → Silent 降级）。返回 sub_maker。"""
        audio_path = self._get_audio_path()
        # v5.x 产物规范前置：导出旁白纯文本（供外部 Agent/工具处理）
        self._save_narration_txt(self._get_narration_text(), audio_path)
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            self._state.combined_audio = audio_path
            logger.info("[MultiScene] audio: file already exists, skipping")
            # 续传：音频已存在则仅重采 cues，避免字幕退回 legacy 启发式
            text = self._get_narration_text()
            return await self._recover_sub_maker(
                text,
                self._state.audio_config,
                self._state.subtitle_config,
                audio_path,
            )

        text = self._get_narration_text()
        if not text:
            logger.info("[MultiScene] audio: empty narration text, skipping")
            return None

        total_duration = sum(float(s.duration) for s in self._state.scenes)
        # Batch 3（S4）：audio_config/subtitle_config 已为 BaseTaskState 共享字段
        audio_config = self._state.audio_config
        subtitle_config = self._state.subtitle_config

        await self._emit("audio", "running", self._t("progress.multi_scene.gen_audio", chars=len(text)), _PROGRESS.audio_end)

        sub_maker = await self._generate_audio_with_fallback(
            output_path=audio_path,
            text=text,
            audio_config=audio_config,
            subtitle_config=subtitle_config,
            duration_sec=total_duration,
            empty_placeholder="",
        )

        self._state.combined_audio = audio_path
        self.task_manager.update_state(combined_audio=audio_path)
        return sub_maker

    async def _generate_subtitles(self, sub_maker: Optional[object] = None) -> None:
        """通用字幕生成（复用 BasePipeline.generate_subtitles_common）。"""
        if not self._state.subtitle_config.enabled:
            return
        texts, durs = self._get_segment_texts_and_durations()
        srt_path, styles_path = await self.generate_subtitles_common(
            segment_texts=texts,
            segment_durations=durs,
            subtitle_config=self._state.subtitle_config,
            sub_maker=sub_maker,
            audio_path=self._state.combined_audio or "",
            screenwriter=self.screenwriter,
            video_width=self._state.video_width,
            video_height=self._state.video_height,
        )
        self._set_subtitle_paths(srt_path, styles_path)

    # ==================================================================
    # 钩子方法（子类可覆盖）
    # ==================================================================

    def _get_init_message(self) -> str:
        return self._t("progress.multi_scene.init")

    def _get_narration_text(self) -> str:
        """配音文本。默认拼接各场景 narration_text。"""
        return "\n\n".join(
            s.narration_text for s in self._state.scenes if s.narration_text
        )

    def _get_segment_texts_and_durations(self) -> tuple:
        """字幕分段文本与时长。默认取各场景 narration_text + duration。"""
        texts = [s.narration_text for s in self._state.scenes if s.narration_text] \
            or [""]
        durs = [float(s.duration) for s in self._state.scenes if s.narration_text] \
            or [5.0]
        return texts, durs

    def _get_audio_path(self) -> str:
        """音频输出路径。子类可覆写（如稿件用 full_narration.mp3）。"""
        return os.path.join(self.working_dir, "combined_narration.mp3")

    def _get_scene_video_prompt(self, scene: SceneTask, index: int) -> str:
        """单场景视频 prompt。

        v7.1.1 关键帧模式：优先 motion_prompt（i2v 动画专用运动描述，构图由
        关键帧锚定）；空串回退 end_frame_prompt / scene_prompt（原行为）。
        """
        if self._keyframes_enabled():
            motion = getattr(scene, "motion_prompt", "")
            if motion:
                return motion
        return getattr(scene, "end_frame_prompt", "") or getattr(scene, "scene_prompt", "")

    def _get_scene_ref_images(self, scene: SceneTask, index: int) -> List[str]:
        """单场景参考图列表。默认取 scene.ref_images。

        v7.1 关键帧模式开启时优先返回该场景关键帧（I2V-first：动画锚定
        在已确认的首帧上；用户显式参考图已被关键帧 i2i 消化或按子类优先级处理）。
        """
        refs = list(getattr(scene, "ref_images", []) or [])
        if self._keyframes_enabled():
            kf = getattr(scene, "keyframe_file", "")
            if kf and os.path.exists(kf):
                return [kf]
        return refs

    def _reference_required(self) -> bool:
        """本流水线是否强制每个片段都带参考图（铁律 No pure Text-to-Video）。

        默认 ``False``：诗词 / 稿件按设计走 T2V（诗词无角色卡，稿件参考图可选），
        强行拦截会破坏既有产品行为。**有角色卡的流水线（creative / anchor）
        必须覆写为 ``True``** —— 那里缺参考图是缺陷，不是可选路径。

        Returns:
            ``True`` 表示缺参考图时阻止提交；``False`` 表示只告警不拦截。
        """
        return False

    async def _guard_scene_reference(self, scene: SceneTask, index: int, refs: List[str]) -> None:
        """提交前校验参考图；强制模式下缺图直接中止，否则记录可见告警。

        Args:
            scene: 当前场景。
            index: 场景下标（0 起）。
            refs: 即将随提交发送的参考图列表。

        Raises:
            PipelineShutdown: ``_reference_required()`` 为 ``True`` 且参考图为空。
        """
        if refs:
            return
        message = self._t("pipeline.reference_required", index=index + 1)
        if self._reference_required():
            raise PipelineShutdown(message)
        # 非强制流水线：不打断任务，但把「这里在跑纯 T2V」写进日志与任务进度，
        # 避免无声降级成人物漂移却没人知道。每条流水线只提示一次。
        logger.warning(
            "[MultiScene] scene %d submits WITHOUT reference image (pure T2V) — "
            "allowed for %s, character consistency is not guaranteed",
            index + 1, type(self).__name__,
        )
        if not getattr(self, "_reference_warned", False):
            self._reference_warned = True
            await self._emit("video_gen", "running", message, 0.40)

    def _get_scene_duration(self, scene: SceneTask, index: int) -> int:
        """单场景视频时长。默认 max(scene.duration, 3)。"""
        return max(int(getattr(scene, "duration", 5)), 3)

    def _set_subtitle_paths(self, srt_path: str, styles_path: str) -> None:
        """字幕路径写回 state。子类覆写以匹配各自字段名。"""
        self._state.combined_subtitle = srt_path
        if styles_path:
            self._state.subtitle_styles_path = styles_path
        self.task_manager.update_state(
            combined_subtitle=srt_path,
            subtitle_styles_path=styles_path or self._state.subtitle_styles_path,
        )
