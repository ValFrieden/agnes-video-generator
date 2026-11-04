"""
core.quality.qc + MultiScene-QC-Schritt — Unit-Tests (v7.2 R8 Batch 2)

Abgedeckt:
- ClipQCGate: PASS/FAIL-Parsing, fail-open bei Chat-Fehler/leerer Antwort/nicht
  extrahierbaren Frames, Frame-Sampling-Aufrufe (fake ffmpeg/ffprobe, hermetisch)
- MultiScenePipeline._run_scene_qc: PASS → keine Neusubmission; FAIL → genau
  eine Regenerierung + Re-Check; qc_report-Buchführung; qc_enabled=False → inaktiv

Alle externen Effekte (ffmpeg, AgnesChat, Video-API) sind gemockt — kein Netz.

Ausführung:
    python -m pytest tests/test_qc_gate.py -v
"""

import asyncio
import os
import sys
import types
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.quality.qc import ClipQCGate, QCVerdict
from models.task import PoetryVideoTask, SceneTask


# ═══════════════════════════════════════════════════
# Hilfskonstruktionen
# ═══════════════════════════════════════════════════


class _FakeChat:
    """chat_multimodal-Stub: liefert geskriptete Antworten, zeichnet Aufrufe auf."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def chat_multimodal(self, system_prompt, text_prompt, image_paths, max_tokens=4096):
        self.calls.append({
            "system": system_prompt, "user": text_prompt, "images": list(image_paths),
        })
        if not self.replies:
            return ""
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def _install_fake_ffmpeg(monkeypatch, *, create_files=True, duration="5.0"):
    """Ersetzt ffmpeg/ffprobe-Auflösung + subprocess.run in core.quality.qc."""
    import core.quality.qc as qc_mod

    calls = {"ffmpeg": [], "ffprobe": 0}

    def fake_run(cmd, **kwargs):
        if cmd[0] == "fake-ffprobe":
            calls["ffprobe"] += 1
            return types.SimpleNamespace(stdout=f"{duration}\n", stderr="")
        calls["ffmpeg"].append(cmd)
        if create_files:
            with open(cmd[-1], "wb") as f:
                f.write(b"\xff\xd8fake-jpg")
        return types.SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(qc_mod, "resolve_ffmpeg", lambda: "fake-ffmpeg")
    monkeypatch.setattr(qc_mod, "resolve_ffprobe", lambda: "fake-ffprobe")
    monkeypatch.setattr(qc_mod.subprocess, "run", fake_run)
    return calls


class TestClipQCGate:
    def _gate(self, replies):
        chat = _FakeChat(replies)
        return ClipQCGate(chat), chat

    def test_pass_verdict(self, tmp_path, monkeypatch):
        _install_fake_ffmpeg(monkeypatch)
        gate, chat = self._gate(["PASS - all frames look good"])
        video = tmp_path / "scene_0" / "video.mp4"
        video.parent.mkdir(parents=True)
        video.write_bytes(b"v")

        verdict = asyncio.run(gate.judge_clip(str(video), "a cat"))

        assert verdict.passed is True
        assert verdict.frames == 5
        assert len(chat.calls) == 1
        # 5 Sample-Frames wurden dem Chat übergeben, Prompt im Nutztext
        assert len(chat.calls[0]["images"]) == 5
        assert "a cat" in chat.calls[0]["user"]

    def test_fail_verdict(self, tmp_path, monkeypatch):
        _install_fake_ffmpeg(monkeypatch)
        gate, _ = self._gate(["FAIL - frame 3 shows a melted face"])
        video = tmp_path / "v.mp4"
        video.write_bytes(b"v")

        verdict = asyncio.run(gate.judge_clip(str(video), "x"))

        assert verdict.passed is False
        assert "melted" in verdict.reason

    def test_fail_open_on_chat_error(self, tmp_path, monkeypatch):
        _install_fake_ffmpeg(monkeypatch)
        gate, _ = self._gate([RuntimeError("chat down")])
        video = tmp_path / "v.mp4"
        video.write_bytes(b"v")

        verdict = asyncio.run(gate.judge_clip(str(video), "x"))

        assert verdict.passed is True
        assert "fail-open" in verdict.reason

    def test_fail_open_on_empty_reply(self, tmp_path, monkeypatch):
        _install_fake_ffmpeg(monkeypatch)
        gate, _ = self._gate([""])
        video = tmp_path / "v.mp4"
        video.write_bytes(b"v")

        verdict = asyncio.run(gate.judge_clip(str(video), "x"))

        assert verdict.passed is True
        assert "empty" in verdict.reason

    def test_fail_open_when_no_frames_extractable(self, tmp_path, monkeypatch):
        _install_fake_ffmpeg(monkeypatch, create_files=False)
        gate, chat = self._gate(["PASS - never called"])
        video = tmp_path / "v.mp4"
        video.write_bytes(b"v")

        verdict = asyncio.run(gate.judge_clip(str(video), "x"))

        assert verdict.passed is True
        assert "manual review" in verdict.reason
        assert chat.calls == []  # kein Chat-Aufruf ohne Frames


# ═══════════════════════════════════════════════════
# MultiScenePipeline._run_scene_qc
# ═══════════════════════════════════════════════════


class _StubTaskManager:
    def __init__(self, task_dir):
        self.task_dir = str(task_dir)
        self.calls = []

    def update_step(self, name, status):
        self.calls.append(("step", name, status))

    def update_state(self, **kwargs):
        self.calls.append(("state", kwargs))

    def create(self, state):
        return state


class _FakeVideoOutput:
    def __init__(self, path=""):
        self.path = path

    async def save(self, path=""):
        path = path or self.path
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("video")
        self.path = path


def _make_qc_pipe(tmp_path, *, scenes=1, qc_enabled=True):
    """MultiScenePipeline-Instanz mit gestubbten Abhängigkeiten bauen."""
    from core.pipelines.multi_scene import MultiScenePipeline

    class _QCConcreteMulti(MultiScenePipeline):
        async def _build_scenes(self):
            return None

        async def _build_reference_images(self):
            return None

        async def _composite_final(self):
            return ""

    state = PoetryVideoTask(
        scenes=[SceneTask(index=i, duration=5) for i in range(scenes)],
        qc_enabled=qc_enabled,
        video_width=768,
        video_height=1152,
    )
    pipe = object.__new__(_QCConcreteMulti)
    pipe.task_manager = _StubTaskManager(tmp_path)
    pipe._state = state
    pipe.task_id = "qc-test"
    pipe.screenwriter = mock.MagicMock()
    pipe.video_api = mock.AsyncMock()
    pipe.video_api.submit_video.return_value = "v-new"
    pipe.video_api.wait_for_video.return_value = _FakeVideoOutput()
    pipe.api_key = "k-test"
    pipe.progress_callback = None
    pipe.shutdown_event = None
    pipe._stop_event = asyncio.Event()
    # working_dir wird über task_manager.task_dir auf tmp_path aufgelöst —
    # Szenen-Clips auf Disk anlegen
    for i in range(scenes):
        d = os.path.join(str(tmp_path), f"scene_{i}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "video.mp4"), "wb") as f:
            f.write(b"v")
    return pipe


class TestSceneQCStep:
    def test_qc_disabled_by_default(self, tmp_path):
        pipe = _make_qc_pipe(tmp_path, qc_enabled=False)
        assert pipe._qc_enabled() is False

    def test_all_pass_no_resubmit(self, tmp_path):
        pipe = _make_qc_pipe(tmp_path, scenes=2)
        gate = mock.MagicMock()
        gate.judge_clip = mock.AsyncMock(return_value=QCVerdict(passed=True, reason="ok"))
        pipe._get_qc_gate = lambda: gate

        asyncio.run(pipe._run_scene_qc())

        assert pipe.video_api.submit_video.await_count == 0
        assert pipe._state.qc_report == {
            "0": {"passed": True, "verdict": "ok"},
            "1": {"passed": True, "verdict": "ok"},
        }

    def test_fail_triggers_single_regen_then_pass(self, tmp_path):
        pipe = _make_qc_pipe(tmp_path, scenes=1)
        gate = mock.MagicMock()
        gate.judge_clip = mock.AsyncMock(side_effect=[
            QCVerdict(passed=False, reason="melted face"),
            QCVerdict(passed=True, reason="fixed"),
        ])
        pipe._get_qc_gate = lambda: gate

        asyncio.run(pipe._run_scene_qc())

        # genau eine Regenerierungs-Submission + Warten + Speichern
        assert pipe.video_api.submit_video.await_count == 1
        assert pipe.video_api.wait_for_video.await_count == 1
        # neues task.json im Szenenverzeichnis (Resume-Id aktualisiert)
        tf = os.path.join(str(tmp_path), "scene_0", "task.json")
        assert os.path.exists(tf) and "v-new" in open(tf, encoding="utf-8").read()
        # finale Konclusion = Re-Check-Ergebnis
        assert pipe._state.qc_report["0"] == {"passed": True, "verdict": "fixed"}
        # Gate wurde 2× befragt (Erstprüfung + Re-Check)
        assert gate.judge_clip.await_count == 2

    def test_still_fail_after_regen_is_flagged_not_fatal(self, tmp_path):
        pipe = _make_qc_pipe(tmp_path, scenes=1)
        gate = mock.MagicMock()
        gate.judge_clip = mock.AsyncMock(side_effect=[
            QCVerdict(passed=False, reason="bad"),
            QCVerdict(passed=False, reason="still bad"),
        ])
        pipe._get_qc_gate = lambda: gate

        asyncio.run(pipe._run_scene_qc())

        assert pipe._state.qc_report["0"] == {"passed": False, "verdict": "still bad"}
        # Clip bleibt bestehen (kein Löschen, manuelle Durchsicht)
        assert os.path.exists(os.path.join(str(tmp_path), "scene_0", "video.mp4"))

    def test_missing_clip_skipped(self, tmp_path):
        pipe = _make_qc_pipe(tmp_path, scenes=1, qc_enabled=True)
        os.remove(os.path.join(str(tmp_path), "scene_0", "video.mp4"))
        gate = mock.MagicMock()
        gate.judge_clip = mock.AsyncMock()
        pipe._get_qc_gate = lambda: gate

        asyncio.run(pipe._run_scene_qc())

        assert gate.judge_clip.await_count == 0
