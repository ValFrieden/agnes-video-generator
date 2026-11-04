"""Befund 10: „Bestätigen und fortsetzen“ darf die hochgeladene Änderung nicht löschen.

Echter Ende-zu-Ende-Lauf ohne Attrappen für die Logik: echter ``TaskManager`` im
temporären Arbeitsordner, echter Abhängigkeitsgraph, echte Endpunkte. Nur das
anschließende ``resume_task`` ist ersetzt (es würde eine Pipeline starten).

Ablauf wie im Frontend (CheckpointDetail): Datei hochladen, danach approve mit
``modified_artifact_ids=[<hochgeladene Datei>]`` und ``confirmed=true``.

Gegenprobe: „Neu generieren“ (``regen``) übergibt die Ergebnisse des Prüfpunkts ebenfalls
als „geändert“, soll sie aber gerade löschen und neu erzeugen.
"""

from __future__ import annotations

import json
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import core.artifacts as artifacts_module
import core.task_manager as task_manager_module
from core.task_manager import TaskManager
from models.task import (
    AudioConfig,
    CreativeVideoTask,
    ManualConfig,
    SceneTask,
    StepStatus,
    SubtitleConfig,
)
from web.routes import task_routes, video_routes

TASK_ID = "t0123456789ab"
ORIGINAL = "ORIGINAL STORY (von der KI)"
USER_EDIT = "MEINE EIGENE GESCHICHTE (vom Nutzer hochgeladen)"


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(task_manager_module, "get_working_dir", lambda: str(tmp_path))
    monkeypatch.setattr(artifacts_module, "get_working_dir", lambda: str(tmp_path))
    monkeypatch.setattr(video_routes, "get_working_dir", lambda: str(tmp_path))
    monkeypatch.setattr(video_routes.helpers, "find_dir_name", lambda tid: tid)

    async def _fake_resume(tid):
        return {"ok": True, "task_id": tid, "resumed": True}

    monkeypatch.setattr(task_routes, "resume_task", _fake_resume)

    tm = TaskManager(TASK_ID, dir_name=TASK_ID)
    state = CreativeVideoTask(
        task_type="creative", creative_name="ut", idea="i", style="s",
        chaining_mode="keyframes", scene_count=2, scene_durations=[5, 5],
        duration_source="manual",
        audio_config=AudioConfig(enabled=True), subtitle_config=SubtitleConfig(enabled=True),
    )
    state.scenes = [SceneTask(index=0), SceneTask(index=1)]
    state.status = StepStatus.PENDING
    state.manual_config = ManualConfig(enabled=True, current_checkpoint="story")
    state.step_story = StepStatus.COMPLETED
    state.step_script = StepStatus.COMPLETED
    tm.create(state)

    story = os.path.join(tm.task_dir, "story.txt")
    with open(story, "w", encoding="utf-8") as f:
        f.write(ORIGINAL)
    state.story_file = story
    tm.update_state(story_file=story)

    app = FastAPI()
    app.include_router(video_routes.router)
    return TestClient(app), tm, story


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_user_edit_survives_approve(env):
    client, tm, story = env

    up = client.post(
        f"/api/tasks/{TASK_ID}/artifacts/creative:story/upload",
        files={"file": ("story.txt", USER_EDIT.encode("utf-8"))},
    )
    assert up.status_code == 200, up.text
    assert _read(story) == USER_EDIT, "Vorbedingung: der Upload hat die Datei überschrieben"

    plan = client.post(
        f"/api/tasks/{TASK_ID}/checkpoints/story/approve",
        data={"modified_artifact_ids": json.dumps(["creative:story"])},
    ).json()

    ok = client.post(
        f"/api/tasks/{TASK_ID}/checkpoints/story/approve",
        data={"modified_artifact_ids": json.dumps(["creative:story"]), "confirmed": "true"},
    )
    assert ok.status_code == 200, ok.text

    after = tm.load()

    assert os.path.exists(story), "die hochgeladene Datei wurde von approve gelöscht"
    assert _read(story) == USER_EDIT
    # Der Schritt bleibt abgeschlossen, damit die Pipeline die Datei übernimmt (SKIP) ...
    assert after.step_story == StepStatus.COMPLETED
    # ... und nur das Abhängige läuft neu.
    assert after.step_script == StepStatus.PENDING
    assert "creative:story" not in plan["affected"]
    assert "creative:script" in plan["affected"]


def test_impact_preview_does_not_list_the_users_own_edit(env):
    """Der Dialog „das wird neu gemacht“ darf die eigene Änderung nicht als Verlust anzeigen."""
    client, _tm, _story = env

    body = client.post(
        f"/api/tasks/{TASK_ID}/checkpoints/story/approve",
        data={"modified_artifact_ids": json.dumps(["creative:story"])},
    ).json()

    assert "creative:story" not in body["affected"]
    assert "creative:story" in body["retained"]


def test_regenerate_still_deletes_and_resets_the_checkpoint_artifacts(env):
    """„Neu generieren“ stützt sich auf das Selbst-Einbeziehen: Es muss weiter löschen
    und darf den Prüfpunkt NICHT als approved markieren (sonst überspringt der Folgelauf die Pause)."""
    client, tm, story = env

    resp = client.post(f"/api/tasks/{TASK_ID}/checkpoints/story/regen")

    assert resp.status_code == 200, resp.text
    assert not os.path.exists(story), "regen muss die Ergebnisse des Prüfpunkts löschen"
    loaded = tm.load()
    assert loaded.step_story == StepStatus.PENDING
    assert "story" not in loaded.manual_config.approved_checkpoints
    assert "creative:story" not in loaded.manual_config.modified_artifacts
