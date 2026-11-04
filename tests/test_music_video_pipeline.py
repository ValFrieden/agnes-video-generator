from unittest.mock import MagicMock
import pytest
from core.audio.beat_detector import calculate_bpm_grid, analyze_audio_track
from core.pipelines.music_video import MusicVideoPipeline
from models.task import MusicVideoTask, TaskType, parse_task_state


def test_calculate_bpm_grid():
    segments = calculate_bpm_grid(total_duration_s=32.0, bpm=120, target_scenes=8)
    assert len(segments) >= 2
    # Verify timings
    assert segments[0].start_time_s == 0.0
    assert segments[-1].end_time_s == 32.0

    energies = [s.energy_level for s in segments]
    assert "low" in energies
    assert "high" in energies  # Must contain a climax/drop segment

    # Check suggested camera movements and transitions
    for s in segments:
        assert s.suggested_camera_movement in ("dolly_in", "tracking_shot", "orbital_pan_cw", "slow_pan")
        assert s.suggested_transition in ("Slow Cross-Dissolve", "Cut", "Whip Pan")


def test_analyze_audio_track_fallback():
    # Fallback when file doesn't exist
    segments = analyze_audio_track("non_existent_audio.mp3", bpm=128, target_scenes=6)
    assert len(segments) >= 2
    assert segments[-1].end_time_s == 30.0


def test_music_video_task_serialization():
    data = {
        "task_id": "mv_test_123",
        "task_type": "music_video",
        "song_title": "Cyberpunk Sunset",
        "bpm": 120,
        "visual_style": "Synthwave Neon",
        "camera_movement": "orbital_pan_cw",
        "draft_mode": True,
    }
    state = parse_task_state(data)
    assert isinstance(state, MusicVideoTask)
    assert state.task_type == TaskType.MUSIC_VIDEO
    assert state.song_title == "Cyberpunk Sunset"
    assert state.bpm == 120
    assert state.camera_movement == "orbital_pan_cw"
    assert state.draft_mode is True


def test_music_video_pipeline_build_scenes():
    task_id = "test_mv_pipe"
    pipeline = MusicVideoPipeline(
        api_key="mock_key",
        task_id=task_id,
        dir_name="tmp_pytest/work",
    )
    state = MusicVideoTask(
        task_id=task_id,
        song_title="Test Anthem",
        bpm=120,
        visual_style="Anime Cyberpunk",
        scene_count=4,
    )
    pipeline._state = state
    pipeline.task_manager = MagicMock()
    pipeline.task_manager.task_dir = "tmp_pytest/work"

    coro = pipeline._build_scenes()
    try:
        coro.send(None)
    except StopIteration:
        pass

    assert state.scene_count >= 2
    assert len(state.scenes) == state.scene_count
    # Verify temporal timeline prompting format [0.0-1.0s] in generated prompts
    for s in state.scenes:
        assert "[0.0-" in s.scene_prompt
        assert "Camera motion:" in s.scene_prompt
        assert s.duration >= 3
