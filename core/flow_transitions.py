"""core/flow_transitions.py — Verwandlung von Foto zu 3D-Figur als EIN Kader.

Veo zwischen zwei sehr verschiedenen Kadern interpolieren zu lassen erzeugt
Sprünge („Phasen“). Dieses Modul macht die Verwandlung stattdessen in ffmpeg aus
zwei **in der Komposition übereinstimmenden** Bildern: ein weicher Übergang, der
vom Gesicht nach außen wächst, mit Ruhephasen davor und danach. Kein Veo, keine
Guthabenpunkte.

Voraussetzung: gleiche Pose, gleicher Maßstab, gleicher Hintergrund. Das prüft
``core.flow_frames.check_pair`` vor dem Rendern.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image


def _ease(p: str) -> str:
    """Smoothstep-Ausdruck für ffmpeg (Fortschritt ``p`` in 0..1)."""
    return f"({p}*{p}*(3-2*{p}))"


def build_morph_filter(
    duration: float = 8.0,
    hold_in: float = 1.0,
    hold_out: float = 2.0,
    center: Tuple[float, float] = (0.53, 0.36),
    reach: float = 1.3,
    softness: float = 0.25,
    size: Tuple[int, int] = (1280, 720),
    fps: int = 25,
) -> str:
    """Filtergraph für Foto → 3D, wachsend aus ``center`` (relative Gesichtsposition).

    Die weiche Maske wird nur in einem Sechzehntel der Pixel berechnet (Viertel
    der Kantenlängen) und dann hochskaliert; ``maskedmerge`` mischt danach
    nativ. Ein Ausdruck je Pixel in voller Größe (``blend=all_expr``) war etwa
    zehnmal langsamer, das Ergebnis ist gleich (die Maske ist ohnehin weich).
    """
    if hold_in < 0 or hold_out < 0 or hold_in + hold_out >= duration:
        raise ValueError("hold_in + hold_out muss kleiner als duration sein")
    w, h = size
    mw, mh = max(2, w // 4), max(2, h // 4)
    span = duration - hold_in - hold_out
    p = f"clip((T-{hold_in})/{span},0,1)"
    s = _ease(p)
    cx, cy = center
    dist = f"hypot((X-{cx}*W)/H,(Y-{cy}*H)/H)/1.2"
    m = f"255*clip(({reach}*{s}-{dist})/{softness},0,1)"
    return (
        f"color=c=black:s={mw}x{mh}:r={fps}:d={duration},format=gray,geq=lum='{m}',"
        f"scale={w}:{h}:flags=bicubic,format=gray[mask];"
        f"[0:v]scale={w}:{h},setsar=1,format=yuv444p[a];"
        f"[1:v]scale={w}:{h},setsar=1,format=yuv444p[b];"
        "[mask]split=1[m];"
        "[a][b][m]maskedmerge,format=yuv420p"
    )


def build_morph_command(
    photo: str,
    toon: str,
    out: str,
    duration: float = 8.0,
    fps: int = 25,
    ffmpeg: str = "ffmpeg",
    **filter_kwargs,
) -> List[str]:
    return [
        ffmpeg, "-y", "-v", "error",
        "-loop", "1", "-framerate", str(fps), "-t", str(duration), "-i", str(photo),
        "-loop", "1", "-framerate", str(fps), "-t", str(duration), "-i", str(toon),
        "-filter_complex", build_morph_filter(duration=duration, fps=fps, **filter_kwargs),
        "-r", str(fps), "-c:v", "libx264", "-crf", "18", "-an", str(out),
    ]


def render_morph(photo: str, toon: str, out: str, check: bool = True, **kwargs) -> str:
    """Rendert das Morphing. Mit ``check`` wird vorher die Komposition geprüft.

    Raises:
        ValueError: Die Bilder passen nicht zusammen (``check``) oder ffmpeg fehlt.
        RuntimeError: ffmpeg schlug fehl.
    """
    if check:
        from core.flow_frames import check_pair

        problems = check_pair(photo, toon)
        if problems:
            raise ValueError("Morphing nicht sinnvoll: " + "; ".join(problems))
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("ffmpeg nicht gefunden")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        build_morph_command(photo, toon, out, ffmpeg=ffmpeg, **kwargs),
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fehlgeschlagen: {proc.stderr[-400:]}")
    return str(out)


def contact_sheet(video: str, out: str, times: Sequence[float], cols: int = 3, cell: Tuple[int, int] = (640, 360)) -> str:
    """Kontaktbogen aus genau ``len(times)`` Kadern (keine Füllzellen)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("ffmpeg nicht gefunden")
    frames: List[Image.Image] = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            png = Path(tmp) / f"f{i}.png"
            proc = subprocess.run(
                [ffmpeg, "-y", "-v", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1",
                 "-vf", f"scale={cell[0]}:{cell[1]}", str(png)],
                capture_output=True, text=True,
            )
            if proc.returncode != 0 or not png.exists():
                raise RuntimeError(f"Kader bei {t}s nicht lesbar: {proc.stderr[-200:]}")
            frames.append(Image.open(png).copy())
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell[0], rows * cell[1]), (0, 0, 0))
    for i, fr in enumerate(frames):
        sheet.paste(fr, ((i % cols) * cell[0], (i // cols) * cell[1]))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=90)
    return str(out)
