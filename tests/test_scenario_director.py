"""Unit tests for ScenarioDirector and scenario generation standard."""

import pytest
from core.screenwriter.scenario_director import (
    ScenarioDirector,
    ScenarioProject,
    CharacterProfile,
    SceneShot
)


def test_calculate_scene_durations_bpm():
    director = ScenarioDirector(api_key="mock_key")
    # 96s with 120 BPM (1 bar = 2.0s). 12 scenes -> 4 bars per scene = 8.0s each
    durations = director.calculate_scene_durations(total_seconds=96.0, bpm=120, target_scenes=12)
    assert len(durations) == 12
    assert sum(durations) == pytest.approx(96.0, 0.01)
    for d in durations:
        assert d == pytest.approx(8.0, 0.1)


def test_calculate_scene_durations_non_even():
    director = ScenarioDirector(api_key="mock_key")
    # 65s total, 5 scenes
    durations = director.calculate_scene_durations(total_seconds=65.0, bpm=None, target_scenes=5)
    assert len(durations) == 5
    assert sum(durations) == pytest.approx(65.0, 0.01)


def test_export_to_markdown():
    director = ScenarioDirector(api_key="mock_key")
    char = CharacterProfile(
        name="John Doe",
        age=32,
        role="Protagonist",
        gender="male",
        appearance="Short dark hair, light stubble",
        wardrobe="Dark slate trench coat",
        anchor_token="A 32-year-old man named John Doe with short dark hair and light stubble wearing a dark slate coat."
    )
    shot = SceneShot(
        scene_number=1,
        start_time_s=0.0,
        end_time_s=8.0,
        duration_s=8.0,
        beat_type="Hook",
        shot_size="Wide Shot",
        camera_movement="Static locked-off",
        lighting_and_color="Edward Hopper lighting",
        environment="Rainy park bench",
        action_description="Lone yellow umbrella on wet bench",
        character_action="No people present",
        symbolic_anchor="Yellow umbrella",
        video_prompt="Wide shot of wet park bench under rain with single yellow umbrella"
    )
    proj = ScenarioProject(
        title="Test Story",
        logline="A test story about hope",
        genre="Cinematic Music Video",
        visual_style="Vintage Gouache",
        bpm=120,
        total_duration_s=8.0,
        character=char,
        shots=[shot]
    )

    md = director.export_to_markdown(proj)
    assert "# 🎬 Режиссёрский сценарий и раскадровка: Test Story" in md
    assert "John Doe" in md
    assert "Yellow umbrella" in md
    assert "Edward Hopper lighting" in md
    assert "00:00 – 00:08" in md
