"""Tests für Paket 1 (Zuverlässigkeit der Flow-Strecke).

Alles läuft gegen Attrappen: kein Browser, keine Guthabenpunkte.

- Anhängen von Referenzbildern prüft die Chip-Anzahl, klickt die Bestätigung nur
  bei Bedarf und entfernt überzählige Chips.
- Selektoren der Anhängen-Strecke bestehen nur aus ASCII (kein „ü“).
- Die Zustandsdatei verhindert ein zweites Absenden und schreibt atomar.
"""

from __future__ import annotations

import asyncio
import json
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

from core.api import google_flow_ui as ui  # noqa: E402
from core.api.google_flow_engine import GoogleFlowEngine  # noqa: E402
from core.flow_shot_state import (  # noqa: E402
    ShotAlreadySubmittedError,
    ShotStateStore,
    ShotStatus,
    prompt_hash,
)

# ── Attrappen ────────────────────────────────────────────────────────────────


class Loc:
    """Locator-Attrappe: ``filter``/``first``/``last`` geben sich selbst zurück."""

    def __init__(self, page, name, visible=True, on_click=None):
        self.page = page
        self.name = name
        self.visible = visible
        self.on_click = on_click
        self.clicks = 0

    def filter(self, **_kw):
        return self

    @property
    def first(self):
        return self

    @property
    def last(self):
        return self

    async def wait_for(self, state="visible", timeout=0):
        if not self.visible:
            raise TimeoutError(f"{self.name} not visible")

    async def click(self, **_kw):
        self.clicks += 1
        if self.on_click:
            self.on_click()


class Keyboard:
    async def press(self, _key):
        return None


class AttachPage:
    """Page-Attrappe mit steuerbarem Verhalten beim Klick aufs Asset."""

    def __init__(self, asset_adds=1, confirm_adds=1, confirm_visible=True, start_chips=0):
        self.chips = start_chips
        self.keyboard = Keyboard()
        self.asset_adds = asset_adds
        self.confirm_adds = confirm_adds
        self.removed = 0
        self.attach_btn = Loc(self, "attach")
        self.asset = Loc(self, "asset", on_click=self._asset_click)
        self.confirm = Loc(self, "confirm", visible=confirm_visible, on_click=self._confirm_click)
        self.chip_remove = Loc(self, "chip-remove", on_click=self._remove_chip)

    def _asset_click(self):
        self.chips += self.asset_adds

    def _confirm_click(self):
        self.chips += self.confirm_adds

    def _remove_chip(self):
        self.chips -= 1
        self.removed += 1

    async def evaluate(self, js):
        assert js == ui.CHIP_COUNT_JS
        return self.chips

    def locator(self, selector):
        table = {
            ui.ATTACH_MEDIA_BUTTON: self.attach_btn,
            ui.ASSET_ITEM: self.asset,
            ui.ADD_TO_PROMPT_BUTTON: self.confirm,
            ui.CHIP_REMOVE_BUTTON: self.chip_remove,
        }
        return table[selector]


@pytest.fixture(autouse=True)
def fast_sleep(monkeypatch):
    real_sleep = asyncio.sleep

    async def _fast(_seconds=0, *a, **kw):
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", _fast)


def make_engine(page):
    engine = GoogleFlowEngine()

    async def _connect(*_a, **_kw):
        return page

    engine.connect = _connect
    return engine


@pytest.fixture
def img(tmp_path) -> str:
    p = tmp_path / "frame.jpg"
    p.write_bytes(b"x")
    return str(p)


# ── Anhängen ─────────────────────────────────────────────────────────────────


async def test_auto_attach_skips_confirm_button(img):
    """Hängt der Klick selbst an, darf die Bestätigung keinen Doppelchip erzeugen."""
    page = AttachPage(asset_adds=1, confirm_visible=True)
    assert await make_engine(page).attach_reference_image(img) is True
    assert page.chips == 1
    assert page.confirm.clicks == 0


async def test_confirm_is_clicked_when_click_did_not_attach(img):
    page = AttachPage(asset_adds=0, confirm_adds=1)
    assert await make_engine(page).attach_reference_image(img) is True
    assert page.chips == 1
    assert page.confirm.clicks == 1


async def test_extra_chip_is_removed(img):
    page = AttachPage(asset_adds=2)
    assert await make_engine(page).attach_reference_image(img) is True
    assert page.chips == 1
    assert page.removed == 1


async def test_attach_fails_loudly_when_no_chip_appears(img):
    page = AttachPage(asset_adds=0, confirm_adds=0, confirm_visible=False)
    with pytest.raises(RuntimeError, match="after retries"):
        await make_engine(page).attach_reference_image(img, max_retries=2)
    assert page.chips == 0


async def test_attach_missing_file_raises(tmp_path):
    page = AttachPage()
    with pytest.raises(FileNotFoundError):
        await make_engine(page).attach_reference_image(str(tmp_path / "nope.jpg"))


async def test_attach_references_checks_total_and_order(tmp_path):
    a, b = tmp_path / "a.jpg", tmp_path / "b.jpg"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    page = AttachPage(asset_adds=1)
    names = []
    engine = make_engine(page)
    original = engine.attach_reference_image

    async def spy(path, *args, **kwargs):
        names.append(Path(path).name)
        return await original(path, *args, **kwargs)

    engine.attach_reference_image = spy
    total = await engine.attach_references([str(a), str(b)])
    assert total == 2
    assert names == ["a.jpg", "b.jpg"]


async def test_clear_prompt_removes_chips_first():
    page = AttachPage(start_chips=3)

    class Editor(Loc):
        async def evaluate(self, _js):
            return {"text": "", "chips": 0}

    editor = Editor(page, "editor")
    orig = page.locator
    page.locator = lambda sel: editor if sel == ui.PROMPT_EDITOR else orig(sel)
    editor_keyboard = page.keyboard
    assert editor_keyboard is not None
    await make_engine(page).clear_prompt()
    assert page.chips == 0
    assert page.removed == 3


# ── Selektoren ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    ["ATTACH_MEDIA_BUTTON", "ASSET_ITEM", "ASSET_TYPE_PATTERN", "ASSET_UPLOAD_BUTTON",
     "ADD_TO_PROMPT_BUTTON", "CHIP_REMOVE_BUTTON", "CHIP_COUNT_JS"],
)
def test_attach_selectors_are_ascii_only(name):
    value = getattr(ui, name)
    assert value.isascii(), f"{name} enthält Nicht-ASCII-Zeichen: {value!r}"


def test_chip_selector_needs_cancel_text():
    """Miniaturen im Chatverlauf heißen auch „Bildelement“, haben aber kein „cancel“."""
    assert "cancel" in ui.CHIP_REMOVE_BUTTON
    assert "cancel" in ui.CHIP_COUNT_JS


# ── Zustandsdatei ────────────────────────────────────────────────────────────


def test_new_shot_is_planned(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    assert store.status("S01") is ShotStatus.PLANNED
    store.guard_submit("S01")  # wirft nicht


def test_guard_blocks_second_submit(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    store.advance("S02", ShotStatus.REQUESTED)
    with pytest.raises(ShotAlreadySubmittedError) as exc:
        store.guard_submit("S02")
    assert exc.value.version == 1


def test_new_version_releases_shot(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    store.advance("S02", ShotStatus.APPROVED, credits=20)
    store.new_version("S02", reason="Ergebnis unbrauchbar")
    store.guard_submit("S02")
    assert store.get("S02")["version"] == 2
    assert store.status("S02") is ShotStatus.PLANNED


def test_status_never_goes_backwards(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    store.advance("S02", ShotStatus.RENDERED)
    with pytest.raises(ValueError):
        store.advance("S02", ShotStatus.KEYFRAME_READY)
    store.advance("S02", ShotStatus.RENDERED)  # gleicher Status ist idempotent


def test_status_only_via_advance(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    with pytest.raises(ValueError):
        store.update("S02", status="DOWNLOADED")


def test_credits_are_summed_over_versions(tmp_path):
    store = ShotStateStore(tmp_path / "shots.json")
    store.advance("S01", ShotStatus.APPROVED, credits=20)
    store.new_version("S01")
    store.advance("S01", ShotStatus.APPROVED, credits=20)
    store.advance("S02", ShotStatus.APPROVED, credits=20)
    assert store.total_credits() == 60
    assert store.total_credits(["S02"]) == 20


def test_state_survives_reload_and_is_valid_json(tmp_path):
    path = tmp_path / "sub" / "shots.json"
    store = ShotStateStore(path)
    store.update("S03", prompt_hash=prompt_hash("a"), clip="clips/clip_03.mp4")
    again = ShotStateStore(path)
    assert again.get("S03")["clip"] == "clips/clip_03.mp4"
    assert json.loads(path.read_text(encoding="utf-8"))["shots"]["S03"]["prompt_hash"] == prompt_hash("a")
    assert not list(path.parent.glob("*.tmp"))


def test_unreadable_state_file_is_not_silently_replaced(tmp_path):
    path = tmp_path / "shots.json"
    path.write_text("{kaputt", encoding="utf-8")
    with pytest.raises(RuntimeError, match="nicht lesbar"):
        ShotStateStore(path).status("S01")


def test_prompt_hash_changes_with_prompt():
    assert prompt_hash("a") != prompt_hash("b")
    assert prompt_hash("a") == prompt_hash("a")



# ── Absenden ─────────────────────────────────────────────────────────────────


class SubmitPage:
    """Page-Attrappe: Klick-Ergebnis und Textverlauf des Eingabefelds sind steuerbar."""

    def __init__(self, clicked=True, texts=("prompt", "")):
        self.clicked = clicked
        self.texts = list(texts)

    async def evaluate(self, js, arg=None):
        if js == ui.SUBMIT_CLICK_JS:
            return self.clicked
        assert js == ui.PROMPT_TEXT_JS
        return self.texts.pop(0) if len(self.texts) > 1 else self.texts[0]


async def test_submit_counts_only_when_field_was_cleared():
    assert await make_engine(SubmitPage(texts=("prompt", ""))).submit_prompt() is True


async def test_submit_reports_failure_when_text_stays():
    """Genau der Fehler vom 27.10.: Klick ging an die falsche Schaltfläche, Text blieb stehen."""
    assert await make_engine(SubmitPage(texts=("prompt", "prompt"))).submit_prompt() is False


async def test_submit_reports_failure_without_button():
    assert await make_engine(SubmitPage(clicked=False)).submit_prompt() is False


async def test_submit_with_empty_field_is_not_questioned():
    assert await make_engine(SubmitPage(texts=("", ""))).submit_prompt() is True
