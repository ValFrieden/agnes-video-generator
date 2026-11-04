"""Tests for features transferred from the watch pipeline and ecosystem skills:
- 5-Element Director Shot Formula & 1-Shot-1-Emotion in ScenarioDirector
- 3D LUT Color Grading in VideoProcessor
- FFmpeg Scene Keyframe detection
- /api/tools/luts endpoint
"""
import os
import pytest
from core.compositor.processor import VideoProcessor
from core.screenwriter.scenario_director import (
    CharacterProfile,
    SceneShot,
    ScenarioDirector,
)

def test_character_profile_prop_anchor():
    char = CharacterProfile(
        name="Valeri",
        age=32,
        role="Protagonist",
        gender="male",
        appearance="Brown hair, grey-green eyes, short stubble",
        wardrobe="Indigo wool coat, dark trousers",
        anchor_token="Caucasian male with brown hair and grey-green eyes",
        prop_anchor="vintage bronze wristwatch with cracked glass"
    )
    assert char.prop_anchor == "vintage bronze wristwatch with cracked glass"


def test_scene_shot_5element_fields():
    shot = SceneShot(
        scene_number=1,
        start_time_s=0.0,
        end_time_s=8.0,
        duration_s=8.0,
        beat_type="Hook",
        shot_size="Wide Shot",
        camera_movement="Slow Push-In",
        lighting_and_color="Chiaroscuro, golden amber rim light",
        environment="Rainy cobblestone alleyway",
        action_description="Walking steadily through the mist",
        character_action="Determined gaze, closed mouth",
        symbolic_anchor="yellow umbrella",
        video_prompt="A wide shot of a man walking in rain",
        emotion="Melancholic determination",
        transition="Match Cut on motion"
    )
    assert shot.emotion == "Melancholic determination"
    assert shot.transition == "Match Cut on motion"


def test_format_5element_prompt():
    director = ScenarioDirector(chat_api=None, api_key="test-key")
    char = CharacterProfile(
        name="Valeri",
        age=32,
        role="Protagonist",
        gender="male",
        appearance="Brown hair",
        wardrobe="Indigo wool coat",
        anchor_token="Caucasian male 32 years old with brown hair and stubble",
        prop_anchor="red wool scarf"
    )
    shot = SceneShot(
        scene_number=1,
        start_time_s=0.0,
        end_time_s=8.0,
        duration_s=8.0,
        beat_type="Hook",
        shot_size="Medium Shot",
        camera_movement="Tracking shot",
        lighting_and_color="Neon reflections on wet asphalt",
        environment="Downtown street at midnight",
        action_description="He gazes at the distant neon sign",
        character_action="Subtle slow breath, eyes tracking upwards",
        symbolic_anchor="",
        video_prompt="Prompt",
        emotion="Quiet longing",
        transition="Whip Pan"
    )
    prompt = director.format_5element_prompt(shot, char)
    assert "[REFERENCE: Subject: Caucasian male" in prompt
    assert "Prop Anchor: red wool scarf" in prompt
    assert "[SCENE: Downtown street at midnight, Lighting: Neon reflections on wet asphalt]" in prompt
    assert "[CAMERA: Medium Shot, Movement: Tracking shot]" in prompt
    assert "[TONE & EMOTION: Quiet longing]" in prompt
    assert "[ACTION: He gazes at the distant neon sign. Character Acting: Subtle slow breath, eyes tracking upwards]" in prompt
    assert "[TRANSITION: Whip Pan]" in prompt


def test_list_available_luts():
    luts = VideoProcessor.list_available_luts()
    assert "cinematic_teal_orange" in luts
    assert "clean_film_anti_plastic" in luts
    assert "warm_vintage" in luts
    for k, v in luts.items():
        assert os.path.isfile(v)
        assert v.endswith(".cube")


def test_apply_lut_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        VideoProcessor.apply_lut("dummy_in.mp4", "non_existent.cube", "dummy_out.mp4")


def test_api_get_luts():
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)
    response = client.get("/api/tools/luts")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    lut_ids = [item["id"] for item in data["luts"]]
    assert "cinematic_teal_orange" in lut_ids
    assert "clean_film_anti_plastic" in lut_ids
    assert "warm_vintage" in lut_ids

