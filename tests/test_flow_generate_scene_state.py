"""generate_scene mit Zustandsdatei, Budget-Policy und Journal.

Attrappen statt Browser. Geprüft wird, dass der Zustand mitläuft und dass ein
zweiter Aufruf desselben Shots nicht erneut absendet (das würde erneut Geld kosten).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

if "playwright" not in sys.modules:  # pragma: no cover - umgebungsabhängig
    try:
        import playwright.async_api  # noqa: F401
    except ImportError:
        pw = types.ModuleType("playwright")
        pw_async = types.ModuleType("playwright.async_api")
        for _name in ("Browser", "BrowserContext", "Page", "Playwright"):
            setattr(pw_async, _name, type(_name, (), {}))
        pw_async.async_playwright = lambda: None
        pw.async_api = pw_async
        sys.modules["playwright"] = pw
        sys.modules["playwright.async_api"] = pw_async

from core.api.google_flow_engine import GoogleFlowEngine  # noqa: E402
from core.api.google_flow_errors import FlowStoppedError  # noqa: E402
from core.flow_budget import BudgetPolicy, CreditLedger  # noqa: E402
from core.flow_shot_state import ShotAlreadySubmittedError, ShotStateStore, ShotStatus  # noqa: E402


class Scripted:
    def __init__(self, tmp_path, confirm_cost=20, confirm_raises=None, render_ok=True):
        self.engine = GoogleFlowEngine()
        self.calls: list[str] = []
        self.target = tmp_path / "clip.mp4"
        e = self.engine

        async def noop(*_a, **_kw):
            return True

        async def zero(*_a, **_kw):
            return 0

        async def submit():
            self.calls.append("submit")
            return True

        async def confirm(previous, max_credits=None, timeout_seconds=120.0, **kw):
            self.calls.append("confirm")
            self.confirm_kwargs = kw
            if confirm_raises:
                raise confirm_raises
            return confirm_cost

        async def wait(initial, **kw):
            return render_ok

        async def download(path, resolution="720p", **kw):
            Path(path).write_bytes(b"x" * 600001)
            return str(path)

        e.ensure_cost_guard_active = noop
        e.exit_editor_if_open = noop
        e.clear_prompt = noop
        e.set_prompt = noop
        e.attach_reference_image = noop
        e.get_video_tiles_count = zero
        e.count_cost_cards = zero
        e.submit_prompt = submit
        e.confirm_within_budget = confirm
        e.wait_for_video_completion = wait
        e.download_latest_video = download
        e.generate_qa_trio = lambda *a, **k: "trio.png"

    async def run(self, **kwargs):
        return await self.engine.generate_scene(
            prompt="a scene", reference_image_path=None, output_clip_path=str(self.target), **kwargs
        )


async def test_state_follows_the_whole_run(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    scripted = Scripted(tmp_path)

    assert await scripted.run(shot_store=store, shot_id="S02") is True

    rec = store.get("S02")
    assert store.status("S02") is ShotStatus.DOWNLOADED
    assert rec["clip"] == str(scripted.target)
    assert rec["prompt_hash"]
    assert [h["status"] for h in rec["history"]] == ["REQUESTED", "APPROVED", "RENDERED", "DOWNLOADED"]
    assert store.total_credits() == 20


async def test_second_run_of_a_submitted_shot_does_not_submit(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    store.advance("S02", ShotStatus.REQUESTED)
    scripted = Scripted(tmp_path)

    with pytest.raises(ShotAlreadySubmittedError):
        await scripted.run(shot_store=store, shot_id="S02")

    assert scripted.calls == []


async def test_blocked_cost_leaves_shot_requested_and_blocks_resubmit(tmp_path):
    """Nach dem Absenden bleibt die Kostenkarte offen: nicht blind wiederholen."""
    store = ShotStateStore(tmp_path / "shots.json")
    scripted = Scripted(tmp_path, confirm_raises=FlowStoppedError("zu teuer", status="cost_blocked"))

    with pytest.raises(FlowStoppedError):
        await scripted.run(shot_store=store, shot_id="S05")

    assert store.status("S05") is ShotStatus.REQUESTED
    with pytest.raises(ShotAlreadySubmittedError):
        store.guard_submit("S05")


async def test_runs_without_state_keep_working(tmp_path):
    scripted = Scripted(tmp_path)
    assert await scripted.run() is True
    assert scripted.confirm_kwargs == {}


async def test_policy_and_ledger_are_passed_through(tmp_path):
    ledger = CreditLedger(tmp_path / "c.jsonl")
    policy = BudgetPolicy(per_clip_max=20)
    scripted = Scripted(tmp_path)

    await scripted.run(policy=policy, ledger=ledger, shot_id="S02", account="second")

    assert scripted.confirm_kwargs == {"policy": policy, "ledger": ledger, "shot_id": "S02", "account": "second"}


async def test_render_timeout_keeps_status_approved(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    scripted = Scripted(tmp_path, render_ok=False)

    assert await scripted.run(shot_store=store, shot_id="S07") is False

    assert store.status("S07") is ShotStatus.APPROVED
    assert store.total_credits() == 20
