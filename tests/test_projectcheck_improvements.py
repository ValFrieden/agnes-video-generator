"""Tests for Projectcheck roadmap implementations (Draft Mode, LUT, MusicVideo route, Assets, LipSync health, Knowledge status)."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

import server
from models.task import MusicVideoTask, parse_task_state


def _client():
    return TestClient(server.app)


def test_music_video_task_step_fields():
    t = MusicVideoTask(task_id="mv1", song_title="Neon")
    assert t.step_build_scenes.value == "pending"
    assert t.step_concatenation.value == "pending"
    restored = parse_task_state(t.model_dump())
    assert isinstance(restored, MusicVideoTask)
    assert restored.song_title == "Neon"


def test_create_creative_draft_mode_enables_pre_video_pause(tmp_path):
    with (
        patch("web.routes.task_creation_routes.get_api_key", return_value="test-key"),
        patch("web.helpers.get_working_dir", return_value=str(tmp_path)),
        patch("core.task_manager.get_working_dir", return_value=str(tmp_path)),
        patch("web.deps.run_pipeline_with_concurrency", return_value=_noop_coro()),
        patch("web.app_state.launch_background_task", side_effect=_close_coro),
    ):
        resp = _client().post(
            "/api/tasks/creative",
            data={
                "idea": "Cyberpunk rainy night",
                "chaining_mode": "keyframes",
                "draft_mode": "true",
                "lut_id": "cinematic_teal_orange",
            },
        )
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]
    from core.task_manager import TaskManager

    with patch("core.task_manager.get_working_dir", return_value=str(tmp_path)):
        dirs = [d.name for d in tmp_path.iterdir() if d.is_dir()]
        state = TaskManager(task_id, dir_name=dirs[0]).load()
    assert state.draft_mode is True
    assert state.lut_id == "cinematic_teal_orange"
    assert state.manual_config.enabled is True
    assert "end_frame_gen" in state.manual_config.pause_points


def test_create_music_video_and_list(tmp_path):
    with (
        patch("web.routes.task_creation_routes.get_api_key", return_value="test-key"),
        patch("web.helpers.get_working_dir", return_value=str(tmp_path)),
        patch("core.task_manager.get_working_dir", return_value=str(tmp_path)),
        patch("web.deps.run_pipeline_with_concurrency", return_value=_noop_coro()),
        patch("web.app_state.launch_background_task", side_effect=_close_coro),
    ):
        resp = _client().post(
            "/api/tasks/music-video",
            data={
                "song_title": "Midnight Drive",
                "bpm": "128",
                "scene_count": "4",
                "visual_style": "35mm Synthwave",
                "lut_id": "warm_vintage",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True

        lst = _client().get("/api/tasks").json()
        assert len(lst["tasks"]) == 1
        assert lst["tasks"][0]["task_type"] == "music_video"
        assert lst["tasks"][0]["song_title"] == "Midnight Drive"
        assert lst["tasks"][0]["bpm"] == 128


def test_workspace_asset_library_crud(tmp_path):
    with (
        patch("web.routes.asset_routes.get_working_dir", return_value=str(tmp_path)),
    ):
        c = _client()
        res = c.post(
            "/api/assets",
            data={
                "name": "Detective Valeri",
                "kind": "character",
                "prompt": "Caucasian male, short brown hair, stubble",
                "continuity_locks": "beige trench coat, no glasses",
            },
            files={"image": ("hero.png", b"\x89PNG\r\n\x1a\nfake", "image/png")},
        )
        assert res.status_code == 200
        asset = res.json()["asset"]
        aid = asset["id"]
        assert asset["image_url"] == f"/api/assets/{aid}/image"

        listed = c.get("/api/assets").json()
        assert len(listed["assets"]) == 1
        assert listed["assets"][0]["name"] == "Detective Valeri"

        img = c.get(asset["image_url"])
        assert img.status_code == 200

        deleted = c.delete(f"/api/assets/{aid}").json()
        assert deleted["ok"] is True
        assert c.get("/api/assets").json()["assets"] == []


def test_lipsync_health_and_knowledge_status():
    c = _client()
    with patch("core.api.lipsync_provider.LivePortraitService.is_available", return_value=False):
        r = c.get("/api/tools/lipsync-health")
        assert r.status_code == 200
        assert r.json()["available"] is False

    ks = c.get("/api/knowledge/status")
    assert ks.status_code == 200
    assert "graph_nodes" in ks.json()["data"]
    assert "graph_edges" in ks.json()["data"]


def test_postprocess_validation(tmp_path):
    with patch("web.routes.video_routes.get_working_dir", return_value=str(tmp_path)):
        r = _client().post("/api/tasks/nonexistent/postprocess", data={"aspect": "9:16"})
        assert r.status_code == 404


async def _noop_coro():
    return None


def _close_coro(coro):
    coro.close()
    return None
