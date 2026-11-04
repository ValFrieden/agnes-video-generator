"""Unit tests for deterministic local frame checks in ClipQCGate."""

import os
import pytest
from PIL import Image
from core.quality.qc import ClipQCGate, QCVerdict


class _DummyChat:
    def chat_multimodal(self, *args, **kwargs):
        return "PASS - dummy"


def test_deterministic_black_frames(tmp_path):
    gate = ClipQCGate(_DummyChat())
    
    # Erzeuge 3 komplett schwarze Testbilder
    frame_paths = []
    for i in range(3):
        p = str(tmp_path / f"black_{i}.jpg")
        img = Image.new("RGB", (64, 64), color=(0, 0, 0))
        img.save(p)
        frame_paths.append(p)
        
    verdict = gate._deterministic_frame_checks(frame_paths)
    assert verdict is not None
    assert verdict.passed is False
    assert "all sampled frames are completely black" in verdict.reason


def test_deterministic_frozen_frames(tmp_path):
    gate = ClipQCGate(_DummyChat())
    
    # Erzeuge 3 komplett identische statische Testbilder (rot)
    frame_paths = []
    for i in range(3):
        p = str(tmp_path / f"static_{i}.jpg")
        img = Image.new("RGB", (64, 64), color=(180, 50, 50))
        img.save(p)
        frame_paths.append(p)
        
    verdict = gate._deterministic_frame_checks(frame_paths)
    assert verdict is not None
    assert verdict.passed is False
    assert "video motion is frozen/static" in verdict.reason


def test_deterministic_healthy_frames(tmp_path):
    gate = ClipQCGate(_DummyChat())
    
    # Erzeuge 3 unterschiedliche, nicht-schwarze Frames mit Bewegung/Änderung
    frame_paths = []
    colors = [(200, 100, 50), (50, 150, 200), (80, 220, 80)]
    for i, c in enumerate(colors):
        p = str(tmp_path / f"motion_{i}.jpg")
        img = Image.new("RGB", (64, 64), color=c)
        img.save(p)
        frame_paths.append(p)
        
    verdict = gate._deterministic_frame_checks(frame_paths)
    # Soll None zurückgeben, damit VLM die inhaltliche Prüfung übernimmt
    assert verdict is None
