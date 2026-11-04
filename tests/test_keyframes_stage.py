"""
v7.1 关键帧模式（I2V-first）单元测试

覆盖（对应 docs/plans/v7.1/i2v_keyframes_PRD.md §六）：
- core/pipelines/multi_scene.py: _generate_scene_keyframes 链式参考序列 / 断点续传跳过
- core/pipelines/manuscript_video.py: 用户逐段参考图优先、关键帧路径同步回 paragraphs、
  开启后视频提交锚定关键帧
- core/pipelines/__init__.py: step_keyframes 检查点注册与顺序
- core/dependency_graph.py: keyframe 依赖边
- core/artifacts.py: keyframe 产物定义

用法:
    .venv/bin/python -m pytest tests/test_keyframes_stage.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

# ═══════════════════════════════════════════════════
# Fakes
# ═══════════════════════════════════════════════════


class _FakeImageOutput:
    async def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"\x89PNG-fake-keyframe")


class _FakeImageAPI:
    def __init__(self):
        self.calls: list[dict] = []

    async def generate_single_image(self, prompt, reference_image_paths=None, size=None, **kw):
        self.calls.append({
            "prompt": prompt,
            "refs": list(reference_image_paths or []),
            "size": size,
        })
        return _FakeImageOutput()


class _FakeVideoOutput:
    async def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"fake-video")


class _FakeVideoAPI:
    def __init__(self):
        self.submits: list[dict] = []

    async def submit_video(self, prompt, reference_image_paths=None, duration=None,
                           width=None, height=None, **kw):
        self.submits.append({
            "prompt": prompt,
            "refs": list(reference_image_paths or []),
        })
        return f"vid_{len(self.submits)}"

    async def wait_for_video(self, video_id, *a, **kw):
        return _FakeVideoOutput()


def _make_manuscript_pipeline(tmp_path, monkeypatch, generate_keyframes=True,
                              reference_images=None):
    """构建隔离工作目录 + 假 API 的稿件流水线（不触网）。"""
    monkeypatch.setenv("AGNES_REGRESSION_WORKING_DIR", str(tmp_path))
    from core.pipelines.manuscript_video import ManuscriptVideoPipeline
    from models.task import ManuscriptParagraph, ManuscriptVideoTask, SceneTask

    p = ManuscriptVideoPipeline(api_key="test-key", task_id="kftest", dir_name="kftest")
    p.image_api = _FakeImageAPI()
    p.video_api = _FakeVideoAPI()

    paragraphs = [
        ManuscriptParagraph(index=i, text=f"第{i}段测试文本内容。", scene_prompt=f"scene {i} prompt")
        for i in range(3)
    ]
    scenes = [
        SceneTask(index=i, scene_prompt=f"scene {i} prompt",
                  narration_text=f"n{i}", duration=5)
        for i in range(3)
    ]
    state = ManuscriptVideoTask(
        task_id="kftest",
        manuscript_text="第0段测试文本内容。第1段测试文本内容。第2段测试文本内容。",
        paragraphs=paragraphs,
        scenes=scenes,
        video_width=768,
        video_height=1152,
        generate_keyframes=generate_keyframes,
        reference_images=reference_images or {},
    )
    p._state = state
    return p, state


# ═══════════════════════════════════════════════════
# 1. 关键帧生成：链式参考 + 断点续传
# ═══════════════════════════════════════════════════


class TestKeyframeGeneration:
    def test_chained_refs_and_paths(self, tmp_path, monkeypatch):
        p, state = _make_manuscript_pipeline(tmp_path, monkeypatch)
        asyncio.run(p._generate_scene_keyframes())

        calls = p.image_api.calls
        assert len(calls) == 3
        # 链式一致性：首场景 t2i（无参考），后续以上一场景关键帧 i2i
        assert calls[0]["refs"] == []
        assert calls[1]["refs"] == [state.scenes[0].keyframe_file]
        assert calls[2]["refs"] == [state.scenes[1].keyframe_file]
        # prompt 复用场景描述；尺寸对齐视频分辨率
        assert calls[0]["prompt"] == "scene 0 prompt"
        assert calls[0]["size"] == "768x1152"
        # 落盘位置：稿件关键帧与段视频同目录（para_{index}）
        for i in range(3):
            kf = state.scenes[i].keyframe_file
            assert kf and os.path.exists(kf)
            assert os.path.normpath(kf).replace("\\", "/").endswith(f"para_{i}/keyframe.png")
            # paragraphs 同步（_generate_videos 按段落读取）
            assert state.paragraphs[i].keyframe_file == kf

    def test_resume_skips_existing(self, tmp_path, monkeypatch):
        p, state = _make_manuscript_pipeline(tmp_path, monkeypatch)
        # 预置第 0 段关键帧（模拟上次运行中断后续传）
        kf0 = os.path.join(p.working_dir, "para_0", "keyframe.png")
        os.makedirs(os.path.dirname(kf0), exist_ok=True)
        with open(kf0, "wb") as f:
            f.write(b"\x89PNG-existing")
        state.scenes[0].keyframe_file = kf0
        state.paragraphs[0].keyframe_file = kf0

        asyncio.run(p._generate_scene_keyframes())

        calls = p.image_api.calls
        assert len(calls) == 2
        # 已存在的第 0 帧跳过生成，但视觉链从它延续
        assert calls[0]["refs"] == [kf0]

    def test_user_refs_take_priority_for_keyframe_i2i(self, tmp_path, monkeypatch):
        user_png = str(tmp_path / "user_ref.png")
        with open(user_png, "wb") as f:
            f.write(b"\x89PNG-user")
        p, state = _make_manuscript_pipeline(
            tmp_path, monkeypatch, reference_images={"1": [user_png]},
        )
        asyncio.run(p._generate_scene_keyframes())

        calls = p.image_api.calls
        # 段 1 的关键帧以用户参考图做 i2i（用户显式输入 > 视觉链）
        assert calls[1]["refs"] == [user_png]
        # 其余段仍走链（段 2 以段 1 的关键帧为参考）
        assert calls[2]["refs"] == [state.scenes[1].keyframe_file]


# ═══════════════════════════════════════════════════
# 2. 视频提交：开启后锚定关键帧（i2v）
# ═══════════════════════════════════════════════════


class TestVideoSubmitUsesKeyframe:
    def test_submit_anchored_on_keyframe(self, tmp_path, monkeypatch):
        p, state = _make_manuscript_pipeline(tmp_path, monkeypatch)
        asyncio.run(p._generate_scene_keyframes())
        asyncio.run(p._generate_videos())

        assert len(p.video_api.submits) == 3
        for i, submit in enumerate(p.video_api.submits):
            assert submit["refs"] == [state.paragraphs[i].keyframe_file]
        # 视频文件已落盘
        for i in range(3):
            assert state.paragraphs[i].video_file and os.path.exists(state.paragraphs[i].video_file)

    def test_disabled_keeps_legacy_refs(self, tmp_path, monkeypatch):
        user_png = str(tmp_path / "user_ref.png")
        with open(user_png, "wb") as f:
            f.write(b"\x89PNG-user")
        p, state = _make_manuscript_pipeline(
            tmp_path, monkeypatch, generate_keyframes=False,
            reference_images={"0": [user_png]},
        )
        asyncio.run(p._generate_videos())

        assert len(p.video_api.submits) == 3
        # 关闭时行为与 v7.1 之前完全一致：仅用户逐段参考图生效
        assert p.video_api.submits[0]["refs"] == [user_png]
        assert p.video_api.submits[1]["refs"] == []
        assert p.video_api.submits[2]["refs"] == []


# ═══════════════════════════════════════════════════
# 4. v7.1.1 静态/运动双提示词
# ═══════════════════════════════════════════════════


class _FakeScreenwriter:
    """按调用计数返回可区分的双提示词 / 单提示词。"""

    def __init__(self):
        self.dual_calls: list[str] = []
        self.single_calls: list[str] = []

    def generate_scene_prompts_for_paragraph_keyframes(self, text, style=""):
        self.dual_calls.append(text)
        return {
            "image_prompt": f"STATIC[{text[:6]}]",
            "motion_prompt": f"MOTION[{text[:6]}]",
        }

    def generate_scene_prompt_for_paragraph(self, text, style=""):
        self.single_calls.append(text)
        return f"SINGLE[{text[:6]}]"


class TestDualPrompts:
    def test_keyframes_mode_uses_dual_prompts(self, tmp_path, monkeypatch):
        p, state = _make_manuscript_pipeline(tmp_path, monkeypatch)
        for para in state.paragraphs:
            para.scene_prompt = ""
        fake_sw = _FakeScreenwriter()
        p.screenwriter = fake_sw

        asyncio.run(p._generate_scene_prompts(state.paragraphs))

        # 关键帧模式：走双提示词方法，不走旧单提示词方法
        assert len(fake_sw.dual_calls) == 3
        assert fake_sw.single_calls == []
        for para in state.paragraphs:
            assert para.scene_prompt.startswith("STATIC[")
            assert para.motion_prompt.startswith("MOTION[")

    def test_disabled_mode_keeps_single_prompt(self, tmp_path, monkeypatch):
        p, state = _make_manuscript_pipeline(
            tmp_path, monkeypatch, generate_keyframes=False,
        )
        for para in state.paragraphs:
            para.scene_prompt = ""
        fake_sw = _FakeScreenwriter()
        p.screenwriter = fake_sw

        asyncio.run(p._generate_scene_prompts(state.paragraphs))

        assert fake_sw.dual_calls == []
        assert len(fake_sw.single_calls) == 3
        for para in state.paragraphs:
            assert para.scene_prompt.startswith("SINGLE[")
            assert para.motion_prompt == ""

    def test_submit_prefers_motion_prompt(self, tmp_path, monkeypatch):
        p, state = _make_manuscript_pipeline(tmp_path, monkeypatch)
        for i, para in enumerate(state.paragraphs):
            para.scene_prompt = f"STATIC[{i}]"
            para.motion_prompt = f"MOTION[{i}]"
            state.scenes[i].scene_prompt = f"STATIC[{i}]"
            state.scenes[i].motion_prompt = f"MOTION[{i}]"
        asyncio.run(p._generate_videos())

        assert len(p.video_api.submits) == 3
        for i, submit in enumerate(p.video_api.submits):
            # i2v 提交用运动提示词；关键帧仍用 scene_prompt（静态）
            assert submit["prompt"] == f"MOTION[{i}]"
            # 本测试未生成关键帧（keyframe_file 空）→ 无参考图
            assert submit["refs"] == []

    def test_submit_falls_back_to_scene_prompt(self, tmp_path, monkeypatch):
        p, state = _make_manuscript_pipeline(tmp_path, monkeypatch)
        # motion 为空（旧任务 / LLM 未返回）→ 回退 scene_prompt
        for i, para in enumerate(state.paragraphs):
            para.motion_prompt = ""
            state.scenes[i].motion_prompt = ""
        asyncio.run(p._generate_videos())

        for submit in p.video_api.submits:
            assert submit["prompt"].startswith("scene ")

    def test_screenwriter_method_normalizes_bad_json(self):
        from core.screenwriter import Screenwriter

        sw = Screenwriter(api_key="test-key")
        sw._chat_json = lambda system, user: {"image_prompt": " ok "}
        result = sw.generate_scene_prompts_for_paragraph_keyframes("段落", "")
        assert result == {"image_prompt": "ok", "motion_prompt": ""}

        sw._chat_json = lambda system, user: "not-a-dict"
        result = sw.generate_scene_prompts_for_paragraph_keyframes("段落", "")
        assert result == {"image_prompt": "", "motion_prompt": ""}


# ═══════════════════════════════════════════════════
# 3. 检查点 / 依赖图 / 产物定义注册
# ═══════════════════════════════════════════════════


class TestRegistration:
    def test_checkpoint_registered_before_videos(self):
        from core.pipelines import (
            _STEP_TO_CHECKPOINT,
            ALL_CHECKPOINTS,
            CHECKPOINT_KEYFRAMES,
        )
        assert CHECKPOINT_KEYFRAMES == "keyframes"
        assert _STEP_TO_CHECKPOINT["step_keyframes"] == "keyframes"
        # compute_current_checkpoint 按 reversed(ALL_CHECKPOINTS) 推断，
        # keyframes 必须位于 videos 之前
        assert ALL_CHECKPOINTS.index("keyframes") < ALL_CHECKPOINTS.index("videos")

    def test_manuscript_keyframes_not_pausable_when_disabled(self, tmp_path, monkeypatch):
        p, _ = _make_manuscript_pipeline(tmp_path, monkeypatch, generate_keyframes=False)
        assert "step_keyframes" not in p._get_pausable_steps()
        p2, _ = _make_manuscript_pipeline(tmp_path, monkeypatch, generate_keyframes=True)
        assert "step_keyframes" in p2._get_pausable_steps()

    def test_dependency_graph_keyframe_edges(self):
        from core.dependency_graph import DependencyGraph
        from models.task import TaskType

        for task_type in (TaskType.MANUSCRIPT, TaskType.POETRY):
            graph = DependencyGraph(task_type)
            # 修改某段关键帧 → 该段视频 + 成片受影响
            assert graph.product_edges["keyframe:{i}"] == {"video", "final_video"}

    def test_artifact_defs_contain_keyframe(self):
        from core.artifacts import _manuscript_artifact_defs, _poetry_artifact_defs

        m_def = [d for d in _manuscript_artifact_defs() if d["type"] == "keyframe"]
        assert m_def and m_def[0]["file"] == "para_{i}/keyframe.png"
        assert m_def[0]["para_fields"] == ["keyframe_file"]

        p_def = [d for d in _poetry_artifact_defs() if d["type"] == "keyframe"]
        assert p_def and p_def[0]["file"] == "scene_{i}/keyframe.png"
        assert p_def[0]["scene_fields"] == ["keyframe_file"]
