"""core.pipelines.creative.pipeline — CreativeVideoPipeline 主类（v5.0 Batch 4 / 4.2 拆分）

四步 mixin（script/frames/video/audio）+ MultiScenePipeline 模板方法组合；
AgnesImageAPI/AgnesVideoAPI 在此模块 import 并实例化（mock 回归 patch 目标）；
图片/视频实际经 provider 工厂按所选模型路由（image_providers/video_providers）。"""
import asyncio
import logging
import os
from typing import Callable, Optional

from core.api.agnes_image import AgnesImageAPI  # noqa: F401  (mock 补丁符号，见 conftest)
from core.api.agnes_video import AgnesVideoAPI  # noqa: F401  (公开符号 + mock 补丁点，见 conftest/测试断言)
from core.api.image_providers import create_image_provider
from core.api.video_providers import create_video_provider
from core.config import DEFAULT_TEXT_MODEL
from core.pipelines import MultiScenePipeline, PipelineShutdown, StepStatus
from core.screenwriter import Screenwriter
from models.task import CreativeVideoTask

from .steps_audio import AudioStepsMixin
from .steps_frames import FramesStepsMixin
from .steps_script import ScriptStepsMixin
from .steps_video import VideoStepsMixin

logger = logging.getLogger(__name__)


class CreativeVideoPipeline(
    ScriptStepsMixin,
    FramesStepsMixin,
    VideoStepsMixin,
    AudioStepsMixin,
    MultiScenePipeline,
):
    """Creative long-form video generation pipeline with audio/subtitle support.

    Generates multi-scene videos from a user idea, with optional TTS narration
    and subtitle overlays.  Supports three chaining modes (``independent``,
    ``chained/ti2vid``, ``keyframes``) and full resume from any completed step.

    Inherits shared infrastructure (progress callbacks, shutdown control,
    task-manager integration) from :class:`BasePipeline`.
    """

    # v5.0 Batch 3（S3，方案 A）：禁用粗粒度步骤级 skip。
    # 本类依赖各 ``_step_*`` 读盘做细粒度断点续传，通过类属性关闭
    # MultiScenePipeline._execute_step 的粗粒度 skip（原覆写已删除，行为一致）。
    coarse_skip = False

    def _reference_required(self) -> bool:
        """创意流水线始终有角色卡 → 缺参考图即缺陷，提交前拦截（铁律 No pure T2V）。"""
        return True

    def _require_character_reference(self) -> None:
        """角色卡缺失时直接中止，绝不提交纯 T2V 片段（铁律）。

        角色卡是整条创意流水线的视觉锚点：没有它，逐场景出图与出片都会各自
        重新想象人物，跨镜头一致性必然崩。宁可失败也不产出漂移的成片。

        Raises:
            PipelineShutdown: 角色卡路径为空或文件已不存在。
        """
        for candidate in (
            getattr(self, "_character_ref_path", ""),
            getattr(self._state, "character_ref_file", ""),
        ):
            if candidate and os.path.exists(candidate):
                return
        raise PipelineShutdown(self._t("pipeline.reference_required", index=1))

    def __init__(
        self,
        api_key: str,
        task_id: str,
        dir_name: Optional[str] = None,
        chat_model: str = DEFAULT_TEXT_MODEL,
        image_model: str = "agnes-image-2.5-flash",
        video_model: str = "agnes-video-v2.0",
        progress_callback: Optional[Callable] = None,
        shutdown_event: Optional[asyncio.Event] = None,
    ):
        """Initialize the creative video pipeline.

        Args:
            api_key: Agnes API key for authentication.
            task_id: Unique identifier for this task.
            dir_name: Optional working-directory name; defaults to *task_id*.
            chat_model: Model name for the screenwriter (LLM chat).
            image_model: Model name for image generation (t2i).
            video_model: Model name for video generation.
            progress_callback: Async callable ``(step, status, message, progress, data)``
                for reporting progress to the caller.
            shutdown_event: External ``asyncio.Event`` that signals a graceful
                shutdown request.
        """
        super().__init__(api_key, task_id, dir_name, progress_callback, shutdown_event)

        # PRD 1.4：Screenwriter language pinning——默认 en、尊重显式配置。
        # 默认中文系统提示词会让模型倾向于输出中文（即使提示词写明"跟随输入语言"），
        # 实测英文/阿拉伯文 idea 在中文提示词下偶发被错误写成中文故事/旁白。
        # 仅当用户未显式设置 PROMPT_LANGUAGE（使用默认 zh）时固定 language="en"；
        # 显式配置代表用户知情选择，以用户配置为准（language=None 走 PROMPT_LANGUAGE）。
        # 补充（2026-08-31 实测）：英文系统提示词下模型仍会因 user prompt 内的中文章节
        # 片段把非中文 idea 写成中文——流水线三处 LLM 调用（故事/脚本/旁白）额外前置
        # 显式语言指令（_style_with_language_directive），与 preview 端点同机制。
        from core.screenwriter import is_prompt_language_explicit

        _sw_language = None if is_prompt_language_explicit() else "en"
        self.screenwriter = Screenwriter(api_key=api_key, model=chat_model, language=_sw_language)
        self.image_generator = create_image_provider(api_key=api_key, model=image_model)
        # v7.1 阶段 2：经 Provider 工厂构建（AGNES_VIDEO_PROVIDER=agnes|fal）
        self.video_generator = create_video_provider(
            api_key=api_key, default_model=video_model, shutdown_event=self.shutdown_event,
        )
        self.video_generator.shutdown_event = self.shutdown_event

        self._state: Optional[CreativeVideoTask] = None

    def _style_with_language_directive(self) -> str:
        """用户 style 前置基于 idea 文字体系的显式语言指令。

        idea 为非中文脚本时返回「指令 + style」，中文 idea 原样返回 style
        （指令为空串）。指令确保故事/旁白跟随输入语言，同时保留"场景视觉提示词
        用英文"的既有约定。
        """
        from core.screenwriter import build_input_language_directive

        return build_input_language_directive(self._state.idea) + self._state.style

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> Optional[CreativeVideoTask]:
        """Current pipeline task state."""
        return self._state

    # ==================================================================
    # v4.0 模板钩子（继承 MultiScenePipeline，复用模板 run() + 步骤编排）
    # ==================================================================
    # Batch 3（S3，方案 A）：不再覆写 _execute_step —— MultiScenePipeline 现支持
    # coarse_skip 开关，本类通过类属性 coarse_skip=False 禁用粗粒度 skip，
    # 依赖各 _step_* 读盘自 skip（保持细粒度 resume，行为与覆写时一致）。

    def _get_init_message(self) -> str:
        return "开始视频生成流程..."

    def _get_watermark_language_text(self) -> str:
        return self._state.idea

    # ------------------------------------------------------------------
    # v6.1：creative 有产物的环节全部可暂停（细粒度检查点）
    # 排除 step_build_scenes / step_reference_images 两个粗粒度合并步骤，
    # 暂停在内部细粒度步骤完成后触发（见下方 _build_scenes / _build_reference_images）。
    # ------------------------------------------------------------------

    def _get_pausable_steps(self) -> set:
        steps = {
            "step_image_analysis",
            "step_story",
            "step_character_ref",
            "step_script",
            "step_end_frame_prompts",
            "step_end_frame_generation",
            "step_video_generation",
            "step_audio",
            "step_subtitle",
            "step_concatenation",
        }
        state = self._state
        if state is not None:
            # 无参考图/尾帧 → 图片分析无实际产物，不暂停
            if not state.reference_image and not state.end_frame_images:
                steps.discard("step_image_analysis")
            # 用户已提供参考图 → 角色参考图直接复用，不生成新图，不暂停
            if state.reference_image:
                steps.discard("step_character_ref")
        return steps

    # ------------------------------------------------------------------
    # 数据来源：分镜（编剧 → story → script → narrations）
    # ------------------------------------------------------------------

    async def _build_scenes(self) -> None:
        """LLM 编剧：场景配置 → 图片分析 → 故事 → 脚本 → 旁白。

        每个有产物的细粒度环节完成后检查手动暂停点（v6.1）。
        """
        await self._step_resolve_scene_config()
        image_context = await self._step_image_analysis(
            self._state.reference_image, self._state.end_frame_images
        )
        self._check_shutdown()
        await self._maybe_pause("step_image_analysis")
        self._story = await self._step_story(image_context)
        self._check_shutdown()
        await self._maybe_pause("step_story")
        self._scenes = await self._step_script(self._story)
        self._check_shutdown()
        await self._step_generate_narrations(self._story, self._scenes)
        self._check_shutdown()
        await self._maybe_pause("step_script")

    # ------------------------------------------------------------------
    # 数据来源：参考图（角色参考 + 尾帧 prompt + 预生成，仅 keyframes 模式）
    # ------------------------------------------------------------------

    async def _build_reference_images(self) -> None:
        """参考图生成：角色参考 → 尾帧 prompt → 预生成（keyframes 模式）。

        每个有产物的细粒度环节完成后检查手动暂停点（v6.1）。
        """
        self._character_ref_path = await self._step_character_reference(self._story)
        self._check_shutdown()
        await self._maybe_pause("step_character_ref")
        self._end_frame_prompts = await self._step_end_frame_prompts(
            self._story, self._scenes
        )
        self._check_shutdown()
        await self._maybe_pause("step_end_frame_prompts")
        self._pregenerated_end_frames = await self._step_pregenerate_end_frames(
            self._scenes, self._end_frame_prompts, self._character_ref_path
        )
        self._check_shutdown()
        await self._maybe_pause("step_end_frame_generation")

    # ------------------------------------------------------------------
    # 视频生成（链式 keyframes / ti2vid / independent — 保留原逻辑）
    # ------------------------------------------------------------------

    # v7.2 R8 质量闸钩子覆写：重生参考图与提交逻辑同源（用户分镜图优先，
    # 其次角色参考图；创意流水线的 scenes 不携带 ref_images 字段）
    def _qc_regen_refs(self, scene, index: int) -> list:
        user_ref = self._user_scene_ref(index)
        if user_ref:
            return [user_ref]
        ref_file = getattr(self._state, "character_ref_file", "") \
            or getattr(self, "_character_ref_path", "")
        return [ref_file] if ref_file and os.path.exists(ref_file) else []

    async def _generate_videos(self) -> None:
        """链式视频生成（覆写通用实现，保留 keyframes/ti2vid/independent 逻辑）。"""
        # 铁律：没有角色卡就不出片——本方法在基类的参考图守卫之外，
        # 必须自己拦一次（三个模式共用同一张角色卡作视觉锚点）。
        self._require_character_reference()
        self._all_video_paths = await self._step_generate_videos(
            self._scenes, self._character_ref_path,
            self._end_frame_prompts, self._pregenerated_end_frames,
        )
        self._check_shutdown()

        # 回写 scenes 状态：通用实现（multi_scene）会在生成时同步
        # scene.video_file / video_status，但链式路径（steps_video）从不回写，
        # 导致 task_state.scenes 始终停在 pending 空值。这里按文件系统补一次
        # 回填，使续传/查询看到真实生成结果。
        scenes = getattr(self._state, "scenes", None)
        if scenes:
            remap = {}
            for idx, path in enumerate(self._all_video_paths):
                remap[idx] = path
            for i, scene in enumerate(scenes):
                if i in remap:
                    scene.video_file = remap[i]
                    scene.video_status = StepStatus.COMPLETED
                    scene.status = StepStatus.COMPLETED
            self.task_manager.update_state(
                scenes=[s.model_dump() for s in scenes],
            )

    # ------------------------------------------------------------------
    # 音频生成（保留原逻辑）
    # ------------------------------------------------------------------

    async def _generate_audio(self) -> object:
        """TTS 配音生成。"""
        sub_maker = await self._step_audio()
        self._check_shutdown()
        return sub_maker

    # ------------------------------------------------------------------
    # 字幕生成（保留原逻辑）
    # ------------------------------------------------------------------

    async def _generate_subtitles(self, sub_maker=None) -> None:
        """字幕生成。"""
        await self._step_subtitle(sub_maker)
        self._check_shutdown()

    # ------------------------------------------------------------------
    # 合成（保留原逻辑）
    # ------------------------------------------------------------------

    async def _composite_final(self) -> str:
        """视频拼接合成。"""
        return await self._step_concatenate(self._all_video_paths)
