"""Tests der Flow-Kommandozeile (Paket 4): Parser, status, check und Schutzregeln.

Kein Browser: ``video`` und ``image`` werden gegen eine Engine-Attrappe geprüft.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest
from PIL import Image

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

from core import flow_pipeline as cli  # noqa: E402
from core.api.google_flow_errors import FlowStoppedError  # noqa: E402
from core.flow_shot_state import ShotStateStore, ShotStatus  # noqa: E402


def make_root(tmp_path: Path) -> Path:
    (tmp_path / "flow_accounts.json").write_text(
        json.dumps({"default": "second", "accounts": {"second": {"index": 3, "project": "abc"}}}),
        encoding="utf-8",
    )
    return tmp_path


def good_frame(path: Path) -> str:
    Image.new("RGB", (1376, 768), (120, 130, 140)).save(path)
    return str(path)


def test_status_lists_shots_and_totals(tmp_path, capsys):
    root = make_root(tmp_path)
    store = ShotStateStore(root / "flow_state" / "shots.json")
    store.advance("S01", ShotStatus.DOWNLOADED, credits=20)
    store.advance("S02", ShotStatus.APPROVED, credits=20)

    assert cli.main(["--root", str(root), "status"]) == 0

    out = capsys.readouterr().out
    assert "S01" in out and "DOWNLOADED" in out and "S02" in out
    assert "Summe laut Shots: 40" in out


def test_check_reports_bad_frame(tmp_path, capsys):
    bad = tmp_path / "p.png"
    Image.new("RGB", (600, 800), (100, 100, 100)).save(bad)
    assert cli.main(["--root", str(tmp_path), "check", "--a", str(bad)]) == 1
    assert "PROBLEM" in capsys.readouterr().out


def test_check_accepts_good_frame(tmp_path, capsys):
    assert cli.main(["--root", str(tmp_path), "check", "--a", good_frame(tmp_path / "g.png")]) == 0
    assert "OK" in capsys.readouterr().out


def test_parser_requires_a_command():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])


def test_video_defaults_to_the_bookable_duration():
    args = cli.build_parser().parse_args(
        ["video", "--shot", "S03", "--frame", "f.jpg", "--motion", "m", "--out", "o.mp4"]
    )
    assert args.seconds == 8 and args.max_clip == 20 and args.budget is None and args.reserve == 0


class FakeEngine:
    """Ersetzt GoogleFlowEngine in der CLI."""

    instances: list["FakeEngine"] = []
    scene_result = True
    scene_error: Exception | None = None

    def __init__(self, *a, **kw):
        self.scene_kwargs = None
        FakeEngine.instances.append(self)

    async def connect(self):
        class P:
            async def goto(self_inner, *a, **kw):
                return None

            class keyboard:
                @staticmethod
                async def press(_k):
                    return None

        return P()

    async def exit_editor_if_open(self):
        return False

    async def read_credit_balance(self):
        return 990

    async def generate_scene(self, **kw):
        self.scene_kwargs = kw
        if FakeEngine.scene_error:
            raise FakeEngine.scene_error
        return FakeEngine.scene_result

    async def generate_image(self, prompt, **kw):
        self.image_prompt = prompt
        self.image_kwargs = kw
        return "out.jpg"

    async def list_characters(self):
        return getattr(FakeEngine, "characters_list", ["Valeri", "Masha"])

    async def create_character(self, name, image_paths, description=None):
        self.created_character = {"name": name, "images": image_paths, "desc": description}
        return True

    async def add_latest_clip_to_scene(self):
        return True

    async def open_scenes_view(self):
        return True

    async def close(self):
        return None


@pytest.fixture
def fake_engine(monkeypatch):
    FakeEngine.instances = []
    FakeEngine.scene_result = True
    FakeEngine.scene_error = None
    monkeypatch.setattr(cli, "GoogleFlowEngine", FakeEngine)

    async def no_sleep(_s):
        return None

    monkeypatch.setattr(cli.asyncio, "sleep", no_sleep)
    return FakeEngine


def run_video(root, frame, *extra):
    return cli.main(
        ["--root", str(root), "video", "--shot", "S03", "--frame", frame,
         "--motion", "Slow pull-back.", "--out", str(root / "clip.mp4"), *extra]
    )


def test_video_passes_state_policy_and_ledger(tmp_path, fake_engine):
    root = make_root(tmp_path)
    assert run_video(root, good_frame(root / "f.png"), "--budget", "100", "--reserve", "50") == 0

    kw = fake_engine.instances[0].scene_kwargs
    assert kw["shot_id"] == "S03" and kw["account"] == "second" and kw["prompt_as_is"] is True
    assert kw["prompt"].startswith("Generate a video with Veo 3.1 Fast, 8 seconds")
    assert (kw["policy"].per_clip_max, kw["policy"].session_budget, kw["policy"].reserve) == (20, 100, 50)
    # Kontostand wurde vor dem ersten Clip ins Journal geschrieben
    assert kw["ledger"].last_balance("second") == 990


def test_video_refuses_bad_start_frame_before_touching_flow(tmp_path, fake_engine, capsys):
    root = make_root(tmp_path)
    bad = root / "p.png"
    Image.new("RGB", (600, 800), (100, 100, 100)).save(bad)

    assert run_video(root, str(bad)) == 1

    assert fake_engine.instances == []
    assert "Startkader" in capsys.readouterr().out


def test_video_reports_stop_and_double_submit(tmp_path, fake_engine, capsys):
    root = make_root(tmp_path)
    frame = good_frame(root / "f.png")

    FakeEngine.scene_error = FlowStoppedError("Budget-Policy: zu teuer", status="budget_blocked")
    assert run_video(root, frame) == 2
    assert "GESTOPPT" in capsys.readouterr().out

    from core.flow_shot_state import ShotAlreadySubmittedError

    FakeEngine.scene_error = ShotAlreadySubmittedError("S03", ShotStatus.REQUESTED, 1)
    assert run_video(root, frame) == 3
    assert "NICHT GESENDET" in capsys.readouterr().out


def test_balance_is_journaled(tmp_path, fake_engine, capsys):
    root = make_root(tmp_path)
    assert cli.main(["--root", str(root), "balance"]) == 0
    assert "990" in capsys.readouterr().out
    lines = (root / "flow_state" / "credits.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[-1])["balance_after"] == 990


def test_character_list_and_create(tmp_path, fake_engine, capsys):
    root = make_root(tmp_path)
    # 1. list
    assert cli.main(["--root", str(root), "character", "list"]) == 0
    out = capsys.readouterr().out
    assert "@Valeri" in out and "@Masha" in out

    # 2. create
    img1 = good_frame(root / "v1.png")
    img2 = good_frame(root / "v2.png")
    assert cli.main(["--root", str(root), "character", "create", "--name", "Valeri", "--images", img1, img2, "--desc", "Caucasian man brown hair"]) == 0
    assert "angelegt" in capsys.readouterr().out
    inst = fake_engine.instances[-1]
    assert inst.created_character["name"] == "Valeri"
    assert len(inst.created_character["images"]) == 2


def test_scene_subcommands(tmp_path, fake_engine, capsys):
    root = make_root(tmp_path)
    assert cli.main(["--root", str(root), "scene", "add"]) == 0
    assert "Clip zur Szene hinzugefügt" in capsys.readouterr().out

    assert cli.main(["--root", str(root), "scene", "open"]) == 0
    assert "Szenen-Ansicht geöffnet" in capsys.readouterr().out


def test_video_passes_character_and_add_to_scene(tmp_path, fake_engine):
    root = make_root(tmp_path)
    frame = good_frame(root / "f.png")
    assert cli.main([
        "--root", str(root), "video",
        "--shot", "S04",
        "--frame", frame,
        "--motion", "Slow zoom in.",
        "--out", str(root / "clip4.mp4"),
        "--character", "Valeri",
        "--add-to-scene",
    ]) == 0

    kw = fake_engine.instances[0].scene_kwargs
    assert kw["character"] == "Valeri"
    assert kw["add_to_scene"] is True
    assert "Featuring @Valeri" in kw["prompt"]


def test_image_passes_character(tmp_path, fake_engine):
    root = make_root(tmp_path)
    ref = good_frame(root / "ref.png")
    assert cli.main([
        "--root", str(root), "image",
        "--prompt", "Valeri standing near birch trees",
        "--character", "Valeri",
        "--ref", ref,
        "--out", str(root / "out.jpg"),
    ]) == 0

    inst = fake_engine.instances[0]
    assert "Featuring @Valeri" in inst.image_prompt
    assert inst.image_kwargs["character"] == "Valeri"
