"""Tests der Google-Flow-Strecke (Logikcheck-Befunde 1–4).

Alles läuft gegen Attrappen: kein Browser, kein Node-Server, keine
Guthabenpunkte. Geprüft wird die Logik, die echtes Geld kostet:

- Befund 1: Sichtbarkeitsprüfung ohne ``.catch`` (JavaScript-Syntax).
- Befund 2: nie 'Immer genehmigen'; Kosten über dem Limit → 'Ablehnen'.
- Befund 3: Zeitablauf → ``FlowPendingError``; ``cost_blocked`` →
  ``FlowStoppedError``.
- Befund 4: nach dem Absenden kein zweiter Versuch; QA-Fehler ist harmlos.
"""

from __future__ import annotations

import asyncio
import json
import sys
import types
from pathlib import Path

import pytest

# Playwright ist in der Testumgebung nicht installiert; die Engine braucht
# davon nur die Typnamen für Annotationen (``from __future__ import annotations``).
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
from core.api.google_flow_errors import FlowPendingError, FlowStoppedError  # noqa: E402

@pytest.fixture(autouse=True)
def short_sleeps(monkeypatch):
    """Die Engine wartet echte Sekunden auf die Oberfläche; in den Tests nicht."""
    real_sleep = asyncio.sleep

    async def _short(seconds=0, *args, **kwargs):
        await real_sleep(min(seconds, 0.01))

    monkeypatch.setattr(asyncio, "sleep", _short)


# ── Attrappen ────────────────────────────────────────────────────────────────


class FakeLocator:
    """Locator-Attrappe mit steuerbarer Sichtbarkeit und Attributen."""

    def __init__(self, visible=True, attrs=None, clicks=None, name=""):
        self._visible = visible
        self._attrs = attrs or {}
        self._clicks = clicks if clicks is not None else []
        self.name = name

    async def wait_for(self, state="visible", timeout=0):
        if not self._visible:
            raise TimeoutError(f"{self.name} not visible")
        return None

    async def get_attribute(self, attr):
        return self._attrs.get(attr)

    async def click(self, **kwargs):
        self._clicks.append(self.name)
        # Nach der Entscheidung gilt die Option als gewählt
        self._attrs["aria-checked"] = "true"

    @property
    def first(self):
        return self

    @property
    def last(self):
        return self


class FakeCard:
    """``flow-permission-message``-Attrappe: liefert Optionen nach aria-label."""

    def __init__(self, available_labels, clicks):
        self._available = available_labels
        self._clicks = clicks

    def locator(self, selector):
        label = selector.split('aria-label="')[1].rstrip('"]')
        return FakeLocator(
            visible=label in self._available,
            attrs=dict(self._available.get(label, {})),
            clicks=self._clicks,
            name=label,
        )

    @property
    def last(self):
        return self

    @property
    def first(self):
        return self


class FakePage:
    """Minimale Page-Attrappe für Kostenkarten-Tests."""

    def __init__(self, body_text="", card_labels=None, bubble=""):
        self.body_text = body_text
        self.clicks: list[str] = []
        self._card = FakeCard(card_labels or {}, self.clicks)
        self._bubble = bubble

    async def inner_text(self, selector):
        return self.body_text

    def locator(self, selector):
        if selector == "flow-permission-message":
            return self._card
        if selector == "flow-chat-bubble":
            return FakeLocator(visible=True, name="bubble")
        return FakeLocator(visible=False, name=selector)


def make_engine(page, **kwargs):
    """Engine mit vorverdrahteter Page-Attrappe (``connect`` wird umgangen)."""
    engine = GoogleFlowEngine(**kwargs)

    async def _connect(*_args, **_kwargs):
        return page

    engine.connect = _connect
    return engine


# ── Befund 1: Sichtbarkeitsprüfung ──────────────────────────────────────────


async def test_visible_true_for_visible_locator():
    assert await GoogleFlowEngine._visible(FakeLocator(visible=True), 100) is True


async def test_visible_false_instead_of_raising():
    """Unsichtbares Element: ``False``, kein AttributeError durch ``.catch``."""
    assert await GoogleFlowEngine._visible(FakeLocator(visible=False), 100) is False


async def test_attach_reference_image_has_no_js_catch():
    """Der ``.catch``-Fehler (Befund 1) darf nicht zurückkommen."""
    source = Path("core/api/google_flow_engine.py").read_text(encoding="utf-8")
    assert ".catch(" not in source


# ── Befund 2: Kostenschutz ──────────────────────────────────────────────────


async def test_approve_never_clicks_always_approve():
    """Auch wenn 'Immer genehmigen' angeboten wird, bleibt es ungeklickt."""
    page = FakePage(card_labels={"Immer genehmigen": {}, "Genehmigen": {}, "Ablehnen": {}})
    engine = make_engine(page)

    assert await engine.approve_cost_card() is True
    assert page.clicks == ["Genehmigen"]
    assert "Immer genehmigen" not in page.clicks


async def test_cost_within_limit_is_approved_once():
    page = FakePage(
        body_text="Soll ich starten? Das kostet 12 Guthabenpunkte.",
        card_labels={"Genehmigen": {}, "Ablehnen": {}, "Immer genehmigen": {}},
    )
    engine = make_engine(page, max_credits=20)

    cost = await engine.confirm_within_budget(previous_card_count=0)

    assert cost == 12
    assert page.clicks == ["Genehmigen"]


async def test_cost_above_limit_is_declined():
    page = FakePage(
        body_text="Das kostet 50 Guthabenpunkte.",
        card_labels={"Genehmigen": {}, "Ablehnen": {}, "Immer genehmigen": {}},
    )
    engine = make_engine(page, max_credits=20)

    with pytest.raises(FlowStoppedError) as excinfo:
        await engine.confirm_within_budget(previous_card_count=0)

    assert excinfo.value.status == "cost_blocked"
    assert page.clicks == ["Ablehnen"]
    assert "Genehmigen" not in page.clicks


async def test_unreadable_cost_card_approves_nothing():
    """Fail closed: ohne lesbaren Preis wird nicht genehmigt."""
    page = FakePage(
        body_text="Agent denkt nach...",
        card_labels={"Genehmigen": {}, "Ablehnen": {}},
    )
    engine = make_engine(page)

    with pytest.raises(FlowStoppedError) as excinfo:
        await engine.confirm_within_budget(previous_card_count=0, timeout_seconds=0.01)

    assert excinfo.value.status == "cost_unreadable"
    assert "Genehmigen" not in page.clicks


async def test_only_new_cost_cards_count():
    """Eine alte Karte im Verlauf gilt nicht als Antwort auf das neue Absenden."""
    page = FakePage(
        body_text="Das kostet 10 Guthabenpunkte.",
        card_labels={"Genehmigen": {}, "Ablehnen": {}},
    )
    engine = make_engine(page)

    with pytest.raises(FlowStoppedError):
        await engine.confirm_within_budget(previous_card_count=1, timeout_seconds=0.01)


async def test_unusual_activity_stops_without_approval():
    page = FakePage(card_labels={"Genehmigen": {}, "Ablehnen": {}})

    engine = make_engine(page)

    async def _bubble_card(previous_count, timeout_seconds=120.0):
        return {"cost": None, "unusual_activity": True, "agent_text": "ungewöhnliche Aktivitäten"}

    engine.wait_for_cost_card = _bubble_card

    with pytest.raises(FlowStoppedError) as excinfo:
        await engine.confirm_within_budget(previous_card_count=0)

    assert excinfo.value.status == "flow_unusual_activity"
    assert "Genehmigen" not in page.clicks


# ── Befund 4: genau einmal absenden ─────────────────────────────────────────


class ScriptedEngine:
    """Verfolgt, wie oft die teuren Schritte aufgerufen werden."""

    def __init__(self, tmp_path, **behaviour):
        self.engine = make_engine(FakePage())
        self.calls: list[str] = []
        self.behaviour = behaviour
        self.target = tmp_path / "clip.mp4"

        e = self.engine

        async def exit_editor_if_open():
            return True

        async def attach(path, **kw):
            self.calls.append("attach")
            return True

        async def set_prompt(text):
            self.calls.append("set_prompt")
            return True

        async def tiles():
            return 0

        async def cards():
            return 0

        async def submit():
            self.calls.append("submit")
            return True

        async def confirm(previous_card_count, max_credits=None, timeout_seconds=120.0):
            self.calls.append("confirm")
            if behaviour.get("confirm_raises"):
                raise behaviour["confirm_raises"]
            return 12

        async def wait_completion(initial, **kw):
            self.calls.append("wait")
            return behaviour.get("render_ok", True)

        async def download(path, resolution="720p", **kw):
            self.calls.append("download")
            if behaviour.get("download_fails"):
                raise RuntimeError("download menu item not found")
            Path(path).write_bytes(b"x" * 600001)
            return str(path)

        def qa(path, output_trio_path=None):
            self.calls.append("qa")
            if behaviour.get("qa_fails"):
                raise FileNotFoundError("ffprobe missing")
            return "trio.png"

        async def ensure_guard():
            self.calls.append("guard")
            if behaviour.get("policy_never"):
                raise FlowStoppedError("policy is Nie", status="confirm_policy_off")

        async def clear():
            self.calls.append("clear")
            return None

        async def mention(name):
            self.calls.append(f"mention:{name}")
            if behaviour.get("mention_fails"):
                raise RuntimeError("no suggestion")

        async def add_scene():
            self.calls.append("add_scene")
            return not behaviour.get("scene_fails")

        e.ensure_cost_guard_active = ensure_guard
        e.clear_prompt = clear
        e.insert_character_mention = mention
        e.add_latest_clip_to_scene = add_scene
        e.exit_editor_if_open = exit_editor_if_open
        e.attach_reference_image = attach
        e.set_prompt = set_prompt
        e.get_video_tiles_count = tiles
        e.count_cost_cards = cards
        e.submit_prompt = submit
        e.confirm_within_budget = confirm
        e.wait_for_video_completion = wait_completion
        e.download_latest_video = download
        e.generate_qa_trio = qa

    async def run(self, **kwargs):
        return await self.engine.generate_scene(
            prompt="a scene",
            reference_image_path=None,
            output_clip_path=str(self.target),
            **kwargs,
        )


async def test_qa_failure_keeps_the_clip(tmp_path):
    """Befund 4: Ein Fehler im QA-Kontaktbogen generiert nicht neu."""
    scripted = ScriptedEngine(tmp_path, qa_fails=True)

    assert await scripted.run() is True
    assert scripted.calls.count("submit") == 1
    assert scripted.target.exists()


async def test_download_failure_does_not_resubmit(tmp_path):
    """Befund 4: Download scheitert → zweiter Downloadversuch, kein neues Absenden."""
    scripted = ScriptedEngine(tmp_path, download_fails=True)

    assert await scripted.run() is False
    assert scripted.calls.count("submit") == 1
    assert scripted.calls.count("download") == 2

    marker = tmp_path / "clip.mp4.flow_pending.json"
    assert marker.exists()
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["status"] == "download_failed"
    assert payload["approved_credits"] == 12


async def test_render_timeout_writes_marker_without_resubmit(tmp_path):
    scripted = ScriptedEngine(tmp_path, render_ok=False)

    assert await scripted.run() is False
    assert scripted.calls.count("submit") == 1
    assert "download" not in scripted.calls
    assert (tmp_path / "clip.mp4.flow_pending.json").exists()


async def test_pending_marker_skips_the_scene(tmp_path):
    """Befund 3: Eine ausstehende Szene wird nicht erneut bezahlt."""
    marker = tmp_path / "clip.mp4.flow_pending.json"
    marker.write_text("{}", encoding="utf-8")
    scripted = ScriptedEngine(tmp_path)

    assert await scripted.run() is False
    assert scripted.calls == []


async def test_cost_blocked_propagates_to_caller(tmp_path):
    """Der Stapel soll anhalten können: FlowStoppedError reicht durch."""
    scripted = ScriptedEngine(
        tmp_path, confirm_raises=FlowStoppedError("too expensive", status="cost_blocked")
    )

    with pytest.raises(FlowStoppedError):
        await scripted.run()
    assert scripted.calls.count("submit") == 1


# ── Befund 3: Wrapper-Timeout und Statusabbildung ───────────────────────────


def test_video_timeout_covers_node_server_budget():
    """Python muss länger warten als der Node-Server rechnet (120 s + 900 s)."""
    from core.api import google_flow

    assert google_flow.VIDEO_TIMEOUT_SECONDS >= 1020


@pytest.mark.parametrize(
    "status",
    ["cost_blocked", "cost_unreadable", "flow_unusual_activity", "decline_failed"],
)
def test_fileless_stopped_statuses_raise_stopped(status):
    from core.api.google_flow import GoogleFlowAPI

    with pytest.raises(FlowStoppedError) as excinfo:
        GoogleFlowAPI._raise_for_fileless_result("Video", {"status": status, "message": "m"})

    assert excinfo.value.status == status


def test_fileless_unknown_status_raises_pending():
    """Unklare Antwort = möglicherweise bezahlt → nicht neu abschicken."""
    from core.api.google_flow import GoogleFlowAPI

    with pytest.raises(FlowPendingError):
        GoogleFlowAPI._raise_for_fileless_result("Video", {"status": "completed"})


# ── Teil C: Einstellungen vor dem Absenden ──────────────────────────────────


async def test_policy_never_stops_before_anything_is_submitted(tmp_path):
    """Bei 'Nie' zahlt Flow schon beim Absenden — also davor abbrechen."""
    scripted = ScriptedEngine(tmp_path, policy_never=True)

    with pytest.raises(FlowStoppedError) as excinfo:
        await scripted.run()

    assert excinfo.value.status == "confirm_policy_off"
    assert "submit" not in scripted.calls
    assert "set_prompt" not in scripted.calls


async def test_prompt_is_cleared_before_references_attach(tmp_path):
    """Sonst bleibt die Figur der vorigen Szene als Chip im Feld."""
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"x")
    scripted = ScriptedEngine(tmp_path)

    await scripted.engine.generate_scene(
        prompt="p", reference_image_path=str(ref), output_clip_path=str(scripted.target)
    )

    assert scripted.calls.index("clear") < scripted.calls.index("attach")


# ── Teil A: Charaktere ──────────────────────────────────────────────────────


async def test_character_mention_is_inserted_after_prompt(tmp_path):
    scripted = ScriptedEngine(tmp_path)

    await scripted.run(character="Anna")

    assert "mention:Anna" in scripted.calls
    assert scripted.calls.index("set_prompt") < scripted.calls.index("mention:Anna")


async def test_unresolved_mention_never_submits(tmp_path):
    """Ein nur getippter @Name hängt keine Referenz an — dann nicht bezahlen."""
    scripted = ScriptedEngine(tmp_path, mention_fails=True)

    assert await scripted.run(character="Anna", max_retries=1) is False
    assert "submit" not in scripted.calls


async def test_create_character_is_idempotent(tmp_path):
    """Gleicher Name erzeugt in Flow sonst einen zweiten Charakter."""
    img = tmp_path / "face.png"
    img.write_bytes(b"x")
    engine = make_engine(FakePage())

    async def existing():
        return ["anna"]

    async def boom():
        raise AssertionError("must not open the page when the name exists")

    engine.list_characters = existing
    engine._open_character_page = boom

    assert await engine.create_character("Anna", [str(img)]) is False


async def test_create_character_rejects_bad_image_counts(tmp_path):
    engine = make_engine(FakePage())
    with pytest.raises(ValueError):
        await engine.create_character("Anna", [])
    with pytest.raises(ValueError):
        await engine.create_character("Anna", ["a.png", "b.png", "c.png"])


async def test_create_character_missing_file(tmp_path):
    engine = make_engine(FakePage())
    with pytest.raises(FileNotFoundError):
        await engine.create_character("Anna", [str(tmp_path / "nope.png")])


def test_project_base_url_strips_subpage():
    url = "https://flow.google.com/project/abc-123/character?x=1"
    assert GoogleFlowEngine._project_base_url(url) == "https://flow.google.com/project/abc-123"


def test_project_base_url_outside_project():
    with pytest.raises(RuntimeError):
        GoogleFlowEngine._project_base_url("https://flow.google.com/")


# ── Teil B: Szenen-Montage ──────────────────────────────────────────────────


async def test_scene_montage_is_added_only_on_request(tmp_path):
    scripted = ScriptedEngine(tmp_path)
    await scripted.run()
    assert "add_scene" not in scripted.calls

    scripted = ScriptedEngine(tmp_path / "b")
    (tmp_path / "b").mkdir()
    await scripted.run(add_to_scene=True)
    assert "add_scene" in scripted.calls


async def test_scene_montage_failure_keeps_the_clip(tmp_path):
    """Unverifizierter Menüeintrag darf einen bezahlten Clip nie entwerten."""
    scripted = ScriptedEngine(tmp_path, scene_fails=True)

    assert await scripted.run(add_to_scene=True) is True
    assert scripted.target.exists()


# ── Selektoren-Modul ────────────────────────────────────────────────────────


def test_always_approve_is_listed_only_as_forbidden():
    from core.api import google_flow_ui as ui

    assert "Immer genehmigen" in ui.COST_ALWAYS_APPROVE_LABELS
    assert "Immer genehmigen" not in ui.COST_APPROVE_LABELS


def test_german_sidebar_labels_are_singular_character():
    """Live geprüft: 'Charakter', nicht das französische 'Personnages'."""
    from core.api import google_flow_ui as ui

    assert 'has-text("Charakter")' in ui.NAV_CHARACTERS
    assert ui.CHARACTER_PATH == "/character"
