"""Tests für den Continuity-Lock- und Review-Standard (Scenario Director).

Deckt ab, was ``review_project`` deterministisch zusichert: fehlende Continuity Locks
im Prompt (SCN-01), leerer Prompt (SCN-02), fehlende Emotion (SCN-03), Lip-Sync-Wörter
(SCN-07), unvollständige Character Bible (SCN-09/SCN-10) und den Block, der aus den
Locks in den Prompt gebaut wird.
"""
import pytest

from core.screenwriter.scenario_director import (
    CharacterProfile,
    ContinuityLock,
    ScenarioDirector,
    ScenarioProject,
    SceneShot,
)

FULL_TURNAROUND = {
    "front": "front face close-up",
    "three_quarter": "three quarter portrait",
    "profile": "side profile",
    "back": "back view",
    "fullbody": "full body standing",
}


def _director() -> ScenarioDirector:
    return ScenarioDirector(api_key="test-key")


def _character(**overrides) -> CharacterProfile:
    base = dict(
        name="Valeri",
        age=32,
        role="Protagonist",
        gender="male",
        appearance="Caucasian, short brown hair, grey-green eyes, stubble",
        wardrobe="Indigo wool overcoat",
        anchor_token="A 32-year-old Caucasian man with short brown hair and grey-green eyes",
        prop_anchor="bronze wristwatch with cracked glass",
        turnaround_prompts=dict(FULL_TURNAROUND),
        continuity_locks=[
            ContinuityLock("identity", "grey-green eyes"),
            ContinuityLock("prop", "bronze wristwatch"),
        ],
    )
    base.update(overrides)
    return CharacterProfile(**base)


def _shot(**overrides) -> SceneShot:
    base = dict(
        scene_number=1,
        start_time_s=0.0,
        end_time_s=8.0,
        duration_s=8.0,
        beat_type="Hook",
        shot_size="Wide Shot",
        camera_movement="Static locked-off",
        lighting_and_color="Chiaroscuro, amber rim light",
        environment="Rainy cobblestone alleyway",
        action_description="He walks through the rain",
        character_action="Closed mouth, slow breathing, eyes tracking",
        symbolic_anchor="yellow umbrella",
        video_prompt="A man with grey-green eyes and a bronze wristwatch holds a yellow umbrella in the rain",
        emotion="Quiet dread",
        transition="Cut",
    )
    base.update(overrides)
    return SceneShot(**base)


def _project(**overrides) -> ScenarioProject:
    base = dict(
        title="Test",
        logline="Test",
        genre="Cinematic",
        visual_style="Hopper",
        total_duration_s=8.0,
        character=_character(),
        shots=[_shot()],
    )
    base.update(overrides)
    return ScenarioProject(**base)


def _ids(issues) -> set:
    return {i.rule_id for i in issues}


def test_continuity_lock_block_lists_all_phrases():
    director = _director()
    block = director.format_continuity_lock_block(_character())
    assert "grey-green eyes" in block
    assert "bronze wristwatch" in block
    assert "copy verbatim" in block


def test_continuity_lock_block_empty_without_locks():
    director = _director()
    assert director.format_continuity_lock_block(_character(continuity_locks=[])) == ""
    assert director.format_continuity_lock_block(None) == ""


def test_clean_project_has_no_issues():
    director = _director()
    assert director.review_project(_project(), requested_scenes=1) == []


def test_missing_lock_in_prompt_is_blocker():
    director = _director()
    shot = _shot(video_prompt="A man walks through the rain")
    issues = director.review_project(_project(shots=[shot]), requested_scenes=1)
    scn01 = [i for i in issues if i.rule_id == "SCN-01"]
    assert len(scn01) == 1
    assert scn01[0].severity == "blocker"
    assert "grey-green eyes" in scn01[0].detail


def test_empty_prompt_is_blocker():
    director = _director()
    issues = director.review_project(_project(shots=[_shot(video_prompt="   ")]), requested_scenes=1)
    assert "SCN-02" in _ids(issues)


def test_missing_emotion_is_blocker():
    director = _director()
    issues = director.review_project(_project(shots=[_shot(emotion="")]), requested_scenes=1)
    assert "SCN-03" in _ids(issues)


def test_lipsync_wording_is_blocker():
    director = _director()
    shot = _shot(character_action="He is speaking directly to camera")
    issues = director.review_project(_project(shots=[shot]), requested_scenes=1)
    assert "SCN-07" in _ids(issues)


def test_missing_anchor_token_is_blocker():
    director = _director()
    proj = _project(character=_character(anchor_token=""))
    assert "SCN-09" in _ids(director.review_project(proj, requested_scenes=1))


def test_incomplete_turnaround_is_blocker():
    director = _director()
    partial = {k: v for k, v in FULL_TURNAROUND.items() if k != "back"}
    proj = _project(character=_character(turnaround_prompts=partial))
    issues = director.review_project(proj, requested_scenes=1)
    scn10 = [i for i in issues if i.rule_id == "SCN-10"]
    assert len(scn10) == 1
    assert "back" in scn10[0].detail


def test_missing_locks_is_warning_not_blocker():
    director = _director()
    proj = _project(character=_character(continuity_locks=[]))
    issues = director.review_project(proj, requested_scenes=1)
    scn11 = [i for i in issues if i.rule_id == "SCN-11"]
    assert len(scn11) == 1
    assert scn11[0].severity == "warning"


def test_empty_shotlist_is_blocker():
    director = _director()
    issues = director.review_project(_project(shots=[]), requested_scenes=1)
    assert _ids(issues) == {"SCN-00"}


def test_markdown_export_contains_review_and_locks():
    director = _director()
    shot = _shot(video_prompt="A man walks through the rain")
    proj = _project(shots=[shot])
    proj.review = director.review_project(proj, requested_scenes=1)

    md = director.export_to_markdown(proj)
    assert "Проверка сценария" in md
    assert "REVISE" in md
    assert "SCN-01" in md
    assert "Continuity Locks" in md
