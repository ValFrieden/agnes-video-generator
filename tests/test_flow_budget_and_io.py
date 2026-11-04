"""Tests für Paket 2 (Budget) und die neuen Ein-/Ausgabewege der Flow-Engine.

Attrappen statt Browser: keine Guthabenpunkte, kein Chrome.

- ``BudgetPolicy``/``CreditLedger``/``FlowAccounts`` aus ``core.flow_budget``.
- ``confirm_within_budget`` mit Policy, Journal und Rückfragen des Agenten.
- ``download_latest_video`` über ``expect_download`` und ``generate_image``.
"""

from __future__ import annotations

import asyncio
import base64
import json
import sys
import types
from types import SimpleNamespace

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

from core.api import google_flow_engine as engine_mod  # noqa: E402
from core.api import google_flow_ui as ui  # noqa: E402
from core.api.google_flow_engine import GoogleFlowEngine  # noqa: E402
from core.api.google_flow_errors import FlowStoppedError  # noqa: E402
from core.flow_budget import BudgetPolicy, CreditLedger, FlowAccounts  # noqa: E402


@pytest.fixture(autouse=True)
def fast_sleep(monkeypatch):
    real_sleep = asyncio.sleep

    async def _fast(_seconds=0, *a, **kw):
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", _fast)


# ── Policy ───────────────────────────────────────────────────────────────────


def test_policy_allows_within_all_limits():
    assert BudgetPolicy(per_clip_max=20, session_budget=100, reserve=50).check(20, spent=40, balance=200) is None


def test_policy_blocks_over_clip_limit():
    assert "Limit pro Clip" in BudgetPolicy(per_clip_max=20).check(25)


def test_policy_blocks_session_budget():
    reason = BudgetPolicy(per_clip_max=20, session_budget=50).check(20, spent=40)
    assert "Gesamtbudget" in reason


def test_policy_blocks_reserve():
    reason = BudgetPolicy(per_clip_max=20, reserve=100).check(20, balance=110)
    assert "Reserve" in reason


def test_policy_unknown_balance_skips_reserve_check():
    assert BudgetPolicy(per_clip_max=20, reserve=1000).check(20, balance=None) is None


# ── Journal ──────────────────────────────────────────────────────────────────


def test_ledger_sums_only_approved_per_account(tmp_path):
    ledger = CreditLedger(tmp_path / "credits.jsonl")
    ledger.record("approved", 20, account="a", shot_id="S01")
    ledger.record("approved", 20, account="a", shot_id="S02")
    ledger.record("blocked", 20, account="a", shot_id="S03")
    ledger.record("approved", 20, account="b")
    assert ledger.spent("a") == 40
    assert ledger.spent() == 60


def test_ledger_last_balance(tmp_path):
    ledger = CreditLedger(tmp_path / "credits.jsonl")
    assert ledger.last_balance("a") is None
    ledger.record("approved", 20, account="a", balance_before=1050, balance_after=1030)
    ledger.record("approved", 20, account="a", balance_before=1030, balance_after=1010)
    assert ledger.last_balance("a") == 1010


def test_ledger_skips_broken_line(tmp_path):
    path = tmp_path / "credits.jsonl"
    ledger = CreditLedger(path)
    ledger.record("approved", 20)
    with path.open("a", encoding="utf-8") as fh:
        fh.write('{"halb\n')
    ledger.record("approved", 20)
    assert ledger.spent() == 40


# ── Konten ───────────────────────────────────────────────────────────────────


def test_accounts_build_project_url(tmp_path):
    cfg = tmp_path / "flow_accounts.json"
    cfg.write_text(
        json.dumps({"default": "second", "accounts": {"second": {"index": 3, "project": "abc"}}}),
        encoding="utf-8",
    )
    accounts = FlowAccounts.load(cfg)
    assert accounts.project_url() == "https://flow.google.com/u/3/project/abc"
    assert accounts.default_name == "second"


def test_accounts_reject_missing_data():
    with pytest.raises(ValueError):
        FlowAccounts({"accounts": {}})
    accounts = FlowAccounts({"accounts": {"x": {"index": 1}}})
    with pytest.raises(ValueError):
        accounts.project_url("x")
    with pytest.raises(KeyError):
        accounts.get("unbekannt")


# ── confirm_within_budget ────────────────────────────────────────────────────


def make_engine(page=None):
    engine = GoogleFlowEngine()

    async def _connect(*_a, **_kw):
        return page

    engine.connect = _connect
    return engine


def wire_card(engine, card):
    calls = []

    async def wait(previous, timeout=120.0):
        return card

    async def approve():
        calls.append("approve")
        return True

    async def reject():
        calls.append("reject")
        return True

    engine.wait_for_cost_card = wait
    engine.approve_cost_card = approve
    engine.reject_cost_card = reject
    return calls


async def test_policy_blocks_and_journals(tmp_path):
    engine = make_engine()
    calls = wire_card(engine, {"cost": 20})
    ledger = CreditLedger(tmp_path / "c.jsonl")
    ledger.record("approved", 20, account="x")
    policy = BudgetPolicy(per_clip_max=20, session_budget=30)

    with pytest.raises(FlowStoppedError) as exc:
        await engine.confirm_within_budget(0, policy=policy, ledger=ledger, shot_id="S03", account="x")

    assert exc.value.status == "budget_blocked"
    assert calls == ["reject"]
    assert ledger.entries()[-1]["action"] == "blocked"
    assert ledger.spent("x") == 20


async def test_approval_is_journaled_with_balance(tmp_path):
    engine = make_engine()
    calls = wire_card(engine, {"cost": 20})
    ledger = CreditLedger(tmp_path / "c.jsonl")
    ledger.record("balance", 0, account="x", balance_after=990)

    cost = await engine.confirm_within_budget(
        0, policy=BudgetPolicy(per_clip_max=20), ledger=ledger, shot_id="S02", account="x"
    )

    assert cost == 20 and calls == ["approve"]
    last = ledger.entries()[-1]
    assert last["action"] == "approved" and last["shot"] == "S02"
    assert last["balance_before"] == 990 and last["balance_after"] == 970


async def test_agent_question_stops_without_clicking():
    engine = make_engine()
    calls = wire_card(engine, {"cost": None, "agent_question": True, "agent_text": "Which option would you prefer?"})
    with pytest.raises(FlowStoppedError) as exc:
        await engine.confirm_within_budget(0)
    assert exc.value.status == "agent_question"
    assert "Which option" in str(exc.value)
    assert calls == []


async def test_policy_per_clip_limit_replaces_default_limit():
    """Ohne Policy gilt das Engine-Limit (20); mit Policy deren per_clip_max."""
    engine = make_engine()
    calls = wire_card(engine, {"cost": 25})
    with pytest.raises(FlowStoppedError) as exc:
        await engine.confirm_within_budget(0)
    assert exc.value.status == "cost_blocked"
    assert calls == ["reject"]

    engine2 = make_engine()
    calls2 = wire_card(engine2, {"cost": 25})
    assert await engine2.confirm_within_budget(0, policy=BudgetPolicy(per_clip_max=30)) == 25
    assert calls2 == ["approve"]


# ── Rückfrage des Agenten beim Warten auf die Kostenkarte ───────────────────


class _Bubble:
    def __init__(self, texts):
        self._texts = list(texts)

    @property
    def last(self):
        return self

    async def inner_text(self):
        return self._texts.pop(0) if len(self._texts) > 1 else self._texts[0]


class _QuestionPage:
    def __init__(self, bubble_texts):
        self._bubble = _Bubble(bubble_texts)

    async def inner_text(self, _selector):
        return "kein Preis hier"

    def locator(self, selector):
        assert selector == "flow-chat-bubble"
        return self._bubble


async def test_wait_returns_question_instead_of_timing_out(monkeypatch):
    clock = {"t": 0.0}

    def fake_time():
        clock["t"] += 6.0
        return clock["t"]

    monkeypatch.setattr(engine_mod, "time", SimpleNamespace(time=fake_time, strftime=__import__("time").strftime))
    page = _QuestionPage(["alte Nachricht", "Veo supports only 8 seconds. Which option would you prefer?"])
    engine = make_engine(page)

    card = await engine.wait_for_cost_card(0, timeout_seconds=300)

    assert card.get("agent_question") is True
    assert "Which option" in card["agent_text"]


# ── Download über expect_download ────────────────────────────────────────────


class _Download:
    async def save_as(self, path):
        with open(path, "wb") as fh:
            fh.write(b"MP4DATA" * 50000)


class _DlCtx:
    def __init__(self, page):
        self.page = page

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False

    @property
    def value(self):
        async def _get():
            return _Download()

        return _get()


class _DownloadPage:
    def __init__(self, editor_open=True):
        self.editor_open = editor_open
        self.tile_clicks = 0
        self.evals = []

    def expect_download(self, timeout=0):
        return _DlCtx(self)

    def locator(self, selector):
        assert selector == ui.DOWNLOAD_MEDIA_BUTTON
        page = self

        class Loc:
            @property
            def first(self_inner):
                return self_inner

            async def wait_for(self_inner, state="visible", timeout=0):
                if not page.editor_open:
                    raise TimeoutError("kein Editor")

        return Loc()

    async def evaluate(self, js, arg=None):
        self.evals.append(js)
        if "flow-video-tile" in js:
            self.tile_clicks += 1
            self.editor_open = True
            return True
        return True


async def test_download_uses_expect_download_and_skips_tile_when_editor_open(tmp_path):
    page = _DownloadPage(editor_open=True)
    engine = make_engine(page)
    engine.downloads_dir = str(tmp_path / "dl")
    target = tmp_path / "out" / "clip.mp4"

    saved = await engine.download_latest_video(str(target))

    assert saved == str(target.resolve())
    assert target.read_bytes() == b"MP4DATA" * 50000
    assert page.tile_clicks == 0
    assert not list(target.parent.glob("*.part"))


async def test_download_opens_tile_when_editor_closed(tmp_path):
    page = _DownloadPage(editor_open=False)
    engine = make_engine(page)
    engine.downloads_dir = str(tmp_path / "dl")

    await engine.download_latest_video(str(tmp_path / "clip.mp4"))

    assert page.tile_clicks == 1


# ── generate_image ───────────────────────────────────────────────────────────

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


class _ImagePage:
    def __init__(self):
        self.srcs = ["old"]
        self.polls = 0

    async def evaluate(self, js, arg=None):
        if js == ui.GENERATED_IMAGE_JS:
            self.polls += 1
            return list(self.srcs) if self.polls < 3 else list(self.srcs) + ["new"]
        return base64.b64encode(PNG).decode()


def wire_image_engine(engine, cost_cards=(0, 0)):
    seq = list(cost_cards)
    calls = []

    async def noop(*_a, **_kw):
        return True

    async def count():
        return seq.pop(0) if len(seq) > 1 else seq[0]

    async def reject():
        calls.append("reject")
        return True

    for name in ("exit_editor_if_open", "clear_prompt", "set_prompt", "submit_prompt", "attach_references"):
        setattr(engine, name, noop)
    engine.count_cost_cards = count
    engine.reject_cost_card = reject
    return calls


async def test_generate_image_saves_new_image(tmp_path):
    engine = make_engine(_ImagePage())
    wire_image_engine(engine)
    out = tmp_path / "img" / "key.jpg"

    path = await engine.generate_image("prompt", output_path=str(out), timeout_seconds=60)

    assert path == str(out)
    assert out.read_bytes() == PNG


async def test_generate_image_never_approves_a_cost_card(tmp_path):
    engine = make_engine(_ImagePage())
    calls = wire_image_engine(engine, cost_cards=(0, 1))
    with pytest.raises(FlowStoppedError) as exc:
        await engine.generate_image("prompt", output_path=str(tmp_path / "x.png"), timeout_seconds=60)
    assert exc.value.status == "image_cost_card"
    assert calls == ["reject"]
