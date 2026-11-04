import pytest

from core.screenwriter.camera_presets import (
    get_all_camera_presets,
    get_camera_preset,
    apply_camera_movement_to_prompt,
    CAMERA_MOVEMENTS,
)
from web.routes.preset_routes import list_camera_movement_presets


def test_all_20_presets_exist_and_valid():
    presets = get_all_camera_presets()
    assert len(presets) == 20
    assert len(CAMERA_MOVEMENTS) == 20

    categories = set()
    ids = set()
    for p in presets:
        assert p.id, "Preset must have an id"
        assert p.id not in ids, f"Duplicate id: {p.id}"
        ids.add(p.id)
        assert p.name_ru and p.name_en
        assert p.category in ("dramatic", "dynamic", "perspective", "atmospheric")
        categories.add(p.category)
        assert len(p.prompt_modifier) > 10
        assert p.icon

    assert categories == {"dramatic", "dynamic", "perspective", "atmospheric"}


def test_get_camera_preset():
    dolly_in = get_camera_preset("dolly_in")
    assert dolly_in is not None
    assert dolly_in.id == "dolly_in"
    assert "dolly push-in" in dolly_in.prompt_modifier.lower()

    vertigo = get_camera_preset("vertigo_zoom")
    assert vertigo is not None
    assert "vertigo contra-zoom" in vertigo.prompt_modifier.lower()

    non_existent = get_camera_preset("non_existent_preset")
    assert non_existent is None


def test_apply_camera_movement_to_prompt():
    raw_prompt = "A mysterious traveler walking through neon rain."
    modified = apply_camera_movement_to_prompt(raw_prompt, "dolly_in")
    assert "Camera execution: Slow, deliberate dolly push-in" in modified

    # Idempotent - does not re-add if already present
    again = apply_camera_movement_to_prompt(modified, "dolly_in")
    assert again == modified

    # None or empty returns untouched
    assert apply_camera_movement_to_prompt(raw_prompt, None) == raw_prompt
    assert apply_camera_movement_to_prompt("", "dolly_in") == ""


def test_camera_presets_api_route():
    data = list_camera_movement_presets()
    assert data["ok"] is True
    assert data["count"] == 20
    assert len(data["presets"]) == 20
    first = data["presets"][0]
    assert "id" in first
    assert "prompt_modifier" in first


def test_syntx_helpers():
    from core.screenwriter.camera_presets import (
        build_stabilizer_clause,
        build_motion_inertia_clause,
        build_storyboard_grid_prompt,
    )
    stab = build_stabilizer_clause()
    assert "Preserve exact facial bone structure" in stab
    assert "Zero facial morphing" in stab

    inertia = build_motion_inertia_clause()
    assert "constant linear velocity" in inertia
    assert "zero sudden acceleration drops" in inertia

    grid = build_storyboard_grid_prompt(["Shot 1", "Shot 2", "Shot 3", "Shot 4"], global_style="Cyberpunk")
    assert "2x2 storyboard collage grid" in grid
    assert "Top-Left (Phase 1): Shot 1" in grid
    assert "Cyberpunk" in grid
