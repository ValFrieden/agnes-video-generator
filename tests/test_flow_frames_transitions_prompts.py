"""Tests für Paket 3: Bildprüfung, Morphing und Prompt-Vorlagen.

Alle Bilder werden synthetisch erzeugt. ffmpeg-Tests laufen nur, wenn ffmpeg
installiert ist.
"""

from __future__ import annotations

import shutil

import pytest
from PIL import Image, ImageDraw

from core import flow_prompts as prompts
from core.flow_frames import MIN_ALIGNMENT, alignment_score, check_frame, check_pair
from core.flow_transitions import build_morph_command, build_morph_filter, contact_sheet, render_morph

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def scene(path, size=(1376, 768), figure_x=0.5, colour=(210, 160, 140), bg=(40, 50, 90)):
    """Hintergrund mit Stufen und einer Figur an ``figure_x`` (Anteil der Breite)."""
    w, h = size
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    d.rectangle((0, int(h * 0.7), w, h), fill=(90, 60, 40))
    d.rectangle((int(w * 0.05), int(h * 0.1), int(w * 0.2), int(h * 0.5)), fill=(120, 110, 80))
    cx = int(w * figure_x)
    d.ellipse((cx - 90, int(h * 0.15), cx + 90, int(h * 0.15) + 220), fill=colour)
    d.rectangle((cx - 140, int(h * 0.15) + 200, cx + 140, h), fill=(150, 180, 220))
    img.save(path)
    return str(path)


# ── Bildprüfung ──────────────────────────────────────────────────────────────


def test_good_frame_has_no_problems(tmp_path):
    assert check_frame(scene(tmp_path / "a.png")).ok


def test_portrait_frame_is_flagged(tmp_path):
    report = check_frame(scene(tmp_path / "p.png", size=(600, 800)))
    assert not report.ok
    assert any("Seitenverhältnis" in p for p in report.problems)
    assert any("Breite" in p for p in report.problems)


def test_pillarbox_is_flagged(tmp_path):
    img = Image.new("RGB", (1376, 768), (0, 0, 0))
    img.paste(Image.new("RGB", (800, 768), (200, 180, 160)), (288, 0))
    path = tmp_path / "pillar.png"
    img.save(path)
    assert any("Pillarbox" in p for p in check_frame(str(path)).problems)


def test_black_frame_is_flagged(tmp_path):
    path = tmp_path / "black.png"
    Image.new("RGB", (1376, 768), (0, 0, 0)).save(path)
    assert any("schwarz" in p for p in check_frame(str(path)).problems)


# ── Ausrichtung ──────────────────────────────────────────────────────────────


def test_same_composition_scores_high_even_with_other_colours(tmp_path):
    a = scene(tmp_path / "a.png")
    b = scene(tmp_path / "b.png", colour=(230, 190, 170), bg=(70, 50, 40))
    assert alignment_score(a, b) > 0.85
    assert check_pair(a, b) == []


def test_moved_figure_scores_low_and_is_reported(tmp_path):
    a = scene(tmp_path / "a.png", figure_x=0.3)
    b = scene(tmp_path / "b.png", figure_x=0.75)
    assert alignment_score(a, b) < MIN_ALIGNMENT
    assert any("Komposition" in p for p in check_pair(a, b))


# ── Morph-Filter ─────────────────────────────────────────────────────────────


def test_morph_filter_is_ascii_and_uses_both_inputs():
    f = build_morph_filter()
    assert f.isascii()
    assert "[0:v]" in f and "[1:v]" in f and "geq=" in f and "maskedmerge" in f


@pytest.mark.parametrize("duration,hold_in,hold_out", [(8, 4, 4), (3, 2, 2), (8, -1, 2)])
def test_morph_filter_rejects_impossible_timing(duration, hold_in, hold_out):
    with pytest.raises(ValueError):
        build_morph_filter(duration=duration, hold_in=hold_in, hold_out=hold_out)


def test_morph_command_sets_duration_and_fps():
    cmd = build_morph_command("a.png", "b.png", "o.mp4", duration=8, fps=25, ffmpeg="ffmpeg")
    assert cmd.count("-t") == 2 and "8" in cmd and "25" in cmd and cmd[-1] == "o.mp4"


def test_render_refuses_misaligned_pair(tmp_path):
    a = scene(tmp_path / "a.png", figure_x=0.3)
    b = scene(tmp_path / "b.png", figure_x=0.75)
    with pytest.raises(ValueError, match="Morphing nicht sinnvoll"):
        render_morph(a, b, str(tmp_path / "o.mp4"))


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg fehlt")
def test_render_and_contact_sheet(tmp_path):
    a = scene(tmp_path / "a.png")
    b = scene(tmp_path / "b.png", colour=(230, 190, 170), bg=(70, 50, 40))
    out = render_morph(a, b, str(tmp_path / "morph.mp4"), duration=3, hold_in=0.5, hold_out=0.5,
                       size=(320, 180), fps=10)
    assert (tmp_path / "morph.mp4").stat().st_size > 1000

    sheet = contact_sheet(out, str(tmp_path / "sheet.jpg"), times=[0.2, 1.0, 1.5, 2.0], cols=3, cell=(320, 180))
    img = Image.open(sheet)
    assert img.size == (960, 360)  # 3 Spalten, 2 Zeilen, genau 4 Kader


# ── Prompts ──────────────────────────────────────────────────────────────────


def test_image_prompt_starts_unambiguously():
    p = prompts.image_prompt("A woman waking up in bed.")
    assert prompts.is_image_prompt(p) and not prompts.is_video_prompt(p)
    assert "Only one character" in p


def test_morph_pair_prompt_demands_same_composition():
    p = prompts.image_prompt("3D version.", same_composition_as_reference=True)
    assert "EXACT same composition" in p


def test_video_prompt_uses_bookable_duration():
    p = prompts.video_prompt("Slow pull-back.", seconds=6)
    assert prompts.is_video_prompt(p)
    assert "8 seconds" in p and "6 seconds" not in p


def test_clips_needed():
    assert prompts.clips_needed(6) == 1
    assert prompts.clips_needed(8) == 1
    assert prompts.clips_needed(8.5) == 2
    assert prompts.clips_needed(16) == 2
    with pytest.raises(ValueError):
        prompts.clips_needed(0)


def test_validate_prompt():
    assert prompts.validate_prompt("hello") is not None
    assert prompts.validate_prompt(prompts.video_prompt("x"), kind="video") is None
    assert prompts.validate_prompt(prompts.video_prompt("x"), kind="image") is not None
