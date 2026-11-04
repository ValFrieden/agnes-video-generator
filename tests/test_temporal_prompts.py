import pytest
from core.screenwriter.scenario_director import (
    ScenarioDirector,
    SceneShot,
    CharacterProfile,
    ContinuityLock,
)
from core.screenwriter.scenes import ScreenwriterScenesMixin


def test_scenario_director_format_temporal_prompt():
    director = ScenarioDirector(api_key="mock-key")
    character = CharacterProfile(
        name="Valeri",
        age=34,
        role="Protagonist",
        gender="male",
        appearance="fair skin, stubble, brown hair, grey-green eyes",
        wardrobe="indigo wool overcoat",
        anchor_token="Caucasian male 34 years old with fair skin, stubble, short matte brown hair, grey-green eyes, wearing indigo wool overcoat.",
        continuity_locks=[
            ContinuityLock(key="identity", phrase="grey-green eyes"),
            ContinuityLock(key="grooming", phrase="short matte brown hair"),
            ContinuityLock(key="wardrobe", phrase="indigo wool overcoat"),
        ],
    )
    shot = SceneShot(
        scene_number=1,
        start_time_s=0.0,
        end_time_s=5.0,
        duration_s=5.0,
        beat_type="Hook",
        shot_size="Medium Shot",
        camera_movement="Slow orbital tracking shot",
        lighting_and_color="Edward Hopper indigo rain and warm amber neon",
        environment="Rainy city street at dusk",
        action_description="Walks through puddle reflections towards illuminated telephone booth",
        character_action="Subtle steady breathing, focused gaze, mouth closed",
        symbolic_anchor="Yellow umbrella",
        video_prompt="Dummy prompt",
        emotion="Melancholic resolve",
        transition="Whip Pan",
    )

    temporal_prompt = director.format_temporal_prompt(shot, character)
    assert "[0.0-" in temporal_prompt
    assert "Establishing frame in Medium Shot" in temporal_prompt
    # Must contain continuity locks verbatim
    assert "grey-green eyes" in temporal_prompt
    assert "short matte brown hair" in temporal_prompt
    assert "indigo wool overcoat" in temporal_prompt
    # Phase 2 must contain camera movement and action
    assert "Slow orbital tracking shot" in temporal_prompt
    assert "Walks through puddle reflections" in temporal_prompt
    # Phase 3 must contain emotion and transition
    assert "Melancholic resolve" in temporal_prompt
    assert "Whip Pan" in temporal_prompt
    assert "mouth firmly closed" in temporal_prompt


def test_screenwriter_scenes_temporal_helper():
    raw = "Cinematic shot of a lone detective in foggy alleys."
    structured = ScreenwriterScenesMixin.format_temporal_prompt_structure(
        raw_prompt=raw,
        duration_s=6.0,
        camera_movement="Dolly push-in",
    )
    assert "[0.0-" in structured
    assert "Establishing shot" in structured
    assert "Dolly push-in" in structured
    assert "detective in foggy alleys" in structured

    # If already formatted with timeline tags, returns unchanged
    already = "[0.0-1.0s]: Scene begins.\n[1.0-3.0s]: Camera moves.\n[3.0-5.0s]: Scene ends."
    assert ScreenwriterScenesMixin.format_temporal_prompt_structure(already) == already
