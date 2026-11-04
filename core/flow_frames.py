"""core/flow_frames.py — Prüfung von Eingangsbildern, bevor sie an Veo gehen.

Zwei Fehler dieser Produktion fielen erst beim Betrachten des fertigen Clips auf:

- ein Hochformat-Kadr (3:4) im 16:9-Video: Veo streckt ihn oder setzt schwarze
  Balken (die „breite Heldin“ in S01);
- ein Kadr mit Wasserzeichen aus der Quelle.

Was sich automatisch prüfen lässt, prüft diese Datei vor dem Hochladen:
Seitenverhältnis, Mindestbreite, schwarze Balken links/rechts bzw. oben/unten und
reine Schwarzbilder. Wasserzeichen lassen sich nicht zuverlässig automatisch
erkennen — das bleibt Sache der Sichtprüfung.

``alignment_score`` bewertet, ob zwei Bilder dieselbe Komposition haben (nötig
für das Morphing: sonst entstehen die „Phasen“ statt einer Verwandlung).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PIL import Image, ImageFilter, ImageOps

ASPECT_16_9 = 16 / 9
# Mit den echten Bildern dieses Projekts kalibriert: Foto und daraus abgeleitete
# 3D-Version derselben Komposition 0.90; das Paar, das in S01 die „Phasen“
# erzeugte (Foto vs. frei erzeugter Keyframe) 0.39–0.43; unverwandte Szenen 0.1.
MIN_ALIGNMENT = 0.6


@dataclass
class FrameReport:
    path: str
    width: int
    height: int
    aspect: float
    problems: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _mean_luma(img: Image.Image, box) -> float:
    region = img.crop(box).convert("L")
    pixels = list(region.getdata())
    return sum(pixels) / max(1, len(pixels))


def check_frame(
    path: str,
    aspect: float = ASPECT_16_9,
    aspect_tolerance: float = 0.02,
    min_width: int = 1280,
    bar_fraction: float = 0.04,
    bar_luma: float = 12.0,
) -> FrameReport:
    """Prüft ein Eingangsbild. ``report.ok`` ist nur wahr, wenn nichts auffiel."""
    img = Image.open(path)
    w, h = img.size
    report = FrameReport(path=str(path), width=w, height=h, aspect=w / h)
    if abs(report.aspect - aspect) / aspect > aspect_tolerance:
        report.problems.append(
            f"Seitenverhältnis {report.aspect:.3f} statt {aspect:.3f}: Veo streckt oder setzt Balken"
        )
    if w < min_width:
        report.problems.append(f"Breite {w} px unter {min_width} px")

    gray = img.convert("L")
    if _mean_luma(gray, (0, 0, w, h)) < 4.0:
        report.problems.append("Bild ist (fast) schwarz")
        return report

    bw, bh = max(2, int(w * bar_fraction)), max(2, int(h * bar_fraction))
    centre = _mean_luma(gray, (w // 4, h // 4, 3 * w // 4, 3 * h // 4))
    if centre > bar_luma * 3:
        if _mean_luma(gray, (0, 0, bw, h)) < bar_luma and _mean_luma(gray, (w - bw, 0, w, h)) < bar_luma:
            report.problems.append("schwarze Balken links und rechts (Pillarbox)")
        if _mean_luma(gray, (0, 0, w, bh)) < bar_luma and _mean_luma(gray, (0, h - bh, w, h)) < bar_luma:
            report.problems.append("schwarze Balken oben und unten (Letterbox)")
    return report


def _edge_map(path: str, size=(64, 36)) -> List[float]:
    img = Image.open(path).convert("L")
    img = ImageOps.autocontrast(img.resize((size[0] * 4, size[1] * 4)))
    edges = img.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(3))
    return [float(v) for v in edges.resize(size).getdata()]


def alignment_score(path_a: str, path_b: str) -> float:
    """Korrelation der Kantenbilder (−1…1). Hoch = gleiche Komposition."""
    a, b = _edge_map(path_a), _edge_map(path_b)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else 0.0


def check_pair(path_a: str, path_b: str, min_alignment: float = MIN_ALIGNMENT) -> List[str]:
    """Gibt die Probleme eines Bildpaars für Start-/Endkader oder Morphing zurück."""
    problems: List[str] = []
    for p in (path_a, path_b):
        for issue in check_frame(p).problems:
            problems.append(f"{Path(p).name}: {issue}")
    score = alignment_score(path_a, path_b)
    if score < min_alignment:
        problems.append(
            f"Komposition passt nicht zusammen (Übereinstimmung {score:.2f} < {min_alignment}): "
            "Pose, Maßstab oder Hintergrund unterscheiden sich, Veo/Morphing bildet Phasen"
        )
    return problems
