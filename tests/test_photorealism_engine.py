"""Unit tests for PhotorealismEngine and 3-Tier Multi-Reference blueprints."""

import pytest
from core.screenwriter.photorealism_engine import (
    PhotorealismEngine,
    LensPreset,
    OpticalArtifacts,
    PhysicalRealityTokens,
    IdentityTransferSpec,
)
from core.screenwriter.scenario_director import (
    ScenarioDirector,
    CharacterProfile,
    SceneShot,
    ScenarioProject,
)


def test_photorealism_engine_enhance():
    engine = PhotorealismEngine(default_lens=LensPreset.CINEMATIC_35MM)
    enhanced = engine.enhance_cinematic_prompt("A man walking through rain")
    
    assert "A man walking through rain" in enhanced
    assert "ARRI Alexa 35" in enhanced
    assert "subtle lens flare" in enhanced
    assert "authentic skin pores" in enhanced
    assert "actor in authentic practical costume" in enhanced


def test_format_identity_transfer_prompt():
    spec = IdentityTransferSpec(
        character_name="Valeri",
        identity_features="grey-blond stubble, grey-green eyes, short brown hair",
        scene_costume_and_style="oil painting by Edmund Blair Leighton, medieval knight chainmail"
    )
    prompt = PhotorealismEngine.format_identity_transfer_prompt(spec)
    
    assert "Keep the exact face, facial structure and immutable identity of Valeri from Reference 2" in prompt
    assert "grey-blond stubble" in prompt
    assert "oil painting by Edmund Blair Leighton" in prompt
    assert "Shot 1: close-up of the face, front view (anfas)" in prompt


def test_format_three_tier_action_prompt():
    prompt = PhotorealismEngine.format_three_tier_action_prompt(
        characters_desc="Knight kneeling on one knee, head bowed",
        environment_desc="Gothic castle hall, warm candle light, dark red tapestry",
        action_and_camera_desc="Slow push-in dolly shot, knight raises gaze to lens",
        duration_s=6.0,
        lens=LensPreset.CINEMATIC_35MM
    )
    
    assert "CHARACTERS:" in prompt
    assert "Knight kneeling on one knee" in prompt
    assert "ENVIRONMENT (recreate precisely, cinematic set lighting):" in prompt
    assert "Gothic castle hall" in prompt
    assert "ACTION & CAMERA (6.0 seconds):" in prompt
    assert "Slow push-in dolly shot" in prompt
    assert "ARRI Alexa 35" in prompt
    assert "Micro-motion cues:" in prompt


def test_scenario_director_integration():
    director = ScenarioDirector(api_key="mock_key")
    char = CharacterProfile(
        name="Elena",
        age=28,
        role="Protagonist",
        gender="female",
        appearance="Dark wavy hair, brown eyes, freckles",
        wardrobe="Ivory trench coat",
        anchor_token="A 28-year-old woman with dark wavy hair and freckles wearing an ivory trench coat."
    )
    shot = SceneShot(
        scene_number=2,
        start_time_s=8.0,
        end_time_s=16.0,
        duration_s=8.0,
        beat_type="Exposition",
        shot_size="Medium Close-Up",
        camera_movement="Slow tracking shot",
        lighting_and_color="Golden hour chiaroscuro",
        environment="Cobblestone city street after rain",
        action_description="Elena looks at reflection in puddle",
        character_action="Thoughtful slight smile, mouth closed",
        symbolic_anchor="Yellow umbrella",
        video_prompt="Elena standing near puddle with yellow umbrella"
    )
    
    tier3 = director.format_scene_prompt_3tier(shot, char)
    assert "CHARACTERS:" in tier3
    assert "A 28-year-old woman with dark wavy hair" in tier3
    assert "Cobblestone city street after rain" in tier3
    assert "Medium Close-Up, Slow tracking shot" in tier3
    
    id_transfer = director.format_identity_transfer(char, "Renaissance fresco style")
    assert "Keep the exact face" in id_transfer
    assert "Elena" in id_transfer
    assert "Renaissance fresco style" in id_transfer
