"""tests.test_vibe_coding_features — Тесты для новых модулей (Kokoro, Remotion, LipSync)."""

import os
import tempfile
import pytest

from core.audio.tts import KokoroTTSEngine
from core.audio.subtitle.remotion_renderer import RemotionSubtitleRenderer
from core.api.lipsync_provider import create_lipsync_provider, LivePortraitService
from models.task import AnchorVideoTask, TaskType


def test_kokoro_voice_and_speed_parsing():
    engine = KokoroTTSEngine()
    
    # Language code inference
    assert engine._infer_lang_code("af_heart") == "a"
    assert engine._infer_lang_code("bf_emma") == "b"
    assert engine._infer_lang_code("zf_xiaobei") == "z"
    assert engine._infer_lang_code("unknown_voice") == "a"

    # Speed parsing
    assert engine._parse_speed("+0%") == 1.0
    assert engine._parse_speed("+20%") == 1.2
    assert engine._parse_speed("-10%") == 0.9
    assert engine._parse_speed("invalid") == 1.0


def test_remotion_srt_parsing():
    sample_srt = """1
00:00:01,000 --> 00:00:03,500
Hello, welcome to Agnes!

2
00:00:04,200 --> 00:00:07,800
This is animated Remotion subtitles.
"""
    with tempfile.NamedTemporaryFile("w", suffix=".srt", delete=False, encoding="utf-8") as f:
        f.write(sample_srt)
        srt_path = f.name

    try:
        items = RemotionSubtitleRenderer.parse_srt(srt_path)
        assert len(items) == 2
        assert items[0]["id"] == 1
        assert items[0]["start"] == 1.0
        assert items[0]["end"] == 3.5
        assert items[0]["text"] == "Hello, welcome to Agnes!"
        assert items[1]["start"] == 4.2
        assert items[1]["end"] == 7.8
    finally:
        if os.path.exists(srt_path):
            os.remove(srt_path)


def test_lipsync_provider_factory():
    provider = create_lipsync_provider("http://test-lipsync:9000/predict")
    assert isinstance(provider, LivePortraitService)
    assert provider.endpoint_url == "http://test-lipsync:9000/predict"


def test_anchor_video_task_lipsync_mode():
    task = AnchorVideoTask(
        task_id="test_anchor_lipsync",
        anchor_prompt="News anchor",
        script_text="Hello world",
        audio_source="lipsync",
    )
    assert task.task_type == TaskType.ANCHOR
    assert task.audio_source == "lipsync"
    
    dumped = task.model_dump()
    assert dumped["audio_source"] == "lipsync"
