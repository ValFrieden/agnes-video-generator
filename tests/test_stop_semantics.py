"""Befund 7 (Logikcheck): Stopp hält die Aufgabe nicht wirklich an.

Jeder Test wurde zuerst gegen den unkorrigierten Code ausgeführt und schlug dort fehl.
Sie laufen ohne Netz, ohne Browser und ohne Guthaben.
"""

from __future__ import annotations

import pytest

# ── Befund 7: Stopp hält die Aufgabe nicht wirklich an ──────────────────────


def test_linked_stop_event_sees_task_stop_and_global_shutdown():
    """Die Anbieter sahen nur das globale Ereignis, nie den Stopp der einzelnen Aufgabe."""
    import asyncio

    from core.pipelines import _LinkedStopEvent

    task_ev, global_ev = asyncio.Event(), asyncio.Event()
    ev = _LinkedStopEvent(task_ev, global_ev)
    assert ev.is_set() is False

    task_ev.set()
    assert ev.is_set() is True

    task_ev.clear()
    global_ev.set()
    assert ev.is_set() is True


def test_linked_stop_event_works_without_global_event():
    import asyncio

    from core.pipelines import _LinkedStopEvent

    task_ev = asyncio.Event()
    ev = _LinkedStopEvent(task_ev, None)
    assert ev.is_set() is False
    task_ev.set()
    assert ev.is_set() is True


@pytest.mark.parametrize(
    ("module", "cls", "provider_attr"),
    [
        ("core.pipelines.simple_video", "SimpleVideoPipeline", "video_api"),
        ("core.pipelines.manuscript_video", "ManuscriptVideoPipeline", "video_api"),
        ("core.pipelines.poetry_video", "PoetryVideoPipeline", "video_api"),
        ("core.pipelines.anchor_video", "AnchorPipeline", "video_generator"),
        ("core.pipelines.creative.pipeline", "CreativeVideoPipeline", "video_generator"),
    ],
)
def test_pipeline_stop_reaches_the_video_provider(module, cls, provider_attr):
    """Stopp einer Aufgabe muss beim Video-Anbieter ankommen, sonst pollt er bis zu 30 min weiter."""
    import asyncio
    import importlib

    pipeline_cls = getattr(importlib.import_module(module), cls)
    pipe = pipeline_cls(
        api_key="k", task_id="t1", dir_name="t1", shutdown_event=asyncio.Event(),
    )
    provider = getattr(pipe, provider_attr)

    assert provider.shutdown_event.is_set() is False
    pipe.stop()
    assert provider.shutdown_event.is_set() is True


async def test_interrupted_pipeline_persists_pending_not_running():
    """Der Zustand im Speicher stand auf RUNNING und überschrieb jedes PENDING des Stopp-Knopfs."""
    from types import SimpleNamespace

    from core.pipelines import PipelineShutdown
    from core.pipelines.simple_video import SimpleVideoPipeline
    from models.task import StepStatus

    saved: list[dict] = []
    pipe = object.__new__(SimpleVideoPipeline)
    pipe.task_manager = SimpleNamespace(
        create=lambda state: None,
        update_state=lambda **kw: saved.append(kw),
    )
    pipe.progress_callback = None
    pipe._t = lambda key, **kw: key

    async def interrupted():
        raise PipelineShutdown("stopped")

    pipe._submit_and_wait = interrupted
    state = SimpleNamespace(
        status=None, current_step="", current_status="", current_progress=0.0,
        current_message="", current_message_key="", current_message_params={},
    )

    with pytest.raises(PipelineShutdown):
        await pipe.run(state)

    assert state.status == StepStatus.PENDING
    assert any(kw.get("status") == StepStatus.PENDING for kw in saved)
    assert not any(kw.get("status") == StepStatus.RUNNING for kw in saved[-2:])


async def test_resume_is_refused_while_the_stopped_pipeline_still_runs(monkeypatch):
    """Resume ersetzte eine gestoppte, noch laufende Pipeline: zwei Schreiber im selben Ordner."""
    import asyncio
    from types import SimpleNamespace

    from fastapi import HTTPException

    from web import app_state
    from web.routes import task_routes

    monkeypatch.setattr(task_routes, "get_api_key", lambda: "k")
    stopped = SimpleNamespace(_stop_event=asyncio.Event())
    stopped._stop_event.set()
    monkeypatch.setitem(app_state.active_pipelines, "t1", stopped)
    monkeypatch.setattr(app_state, "_queued_tasks", {})

    with pytest.raises(HTTPException) as excinfo:
        await task_routes.resume_task("t1")

    assert excinfo.value.status_code == 409
    assert app_state.active_pipelines["t1"] is stopped  # nicht ersetzt


async def test_resume_may_replace_a_stopped_pipeline_that_is_still_queued(monkeypatch):
    """Eine gestoppte Aufgabe in der Warteschlange hält keinen Slot: Ersetzen bleibt harmlos,
    sonst wäre sie womöglich minutenlang nicht fortsetzbar."""
    import asyncio
    from types import SimpleNamespace

    from fastapi import HTTPException

    from web import app_state
    from web.routes import task_routes

    monkeypatch.setattr(task_routes, "get_api_key", lambda: "k")
    stopped = SimpleNamespace(_stop_event=asyncio.Event())
    stopped._stop_event.set()
    monkeypatch.setitem(app_state.active_pipelines, "t2", stopped)
    monkeypatch.setattr(app_state, "_queued_tasks", {"t2": 1})
    monkeypatch.setattr(task_routes.helpers, "find_dir_name", lambda tid: tid)

    class _NoTask:
        def __init__(self, *a, **k): ...
        def load(self):
            return None

    monkeypatch.setattr(task_routes, "TaskManager", _NoTask)

    with pytest.raises(HTTPException) as excinfo:
        await task_routes.resume_task("t2")

    # Es kam an der Stopp-Prüfung vorbei und scheitert erst beim fehlenden Task (404), nicht mit 409.
    assert excinfo.value.status_code == 404
