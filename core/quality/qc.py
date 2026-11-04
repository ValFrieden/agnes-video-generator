"""core.quality.qc — VLM-Qualitätsgate für generierte Szenenclips (v7.2 R8 Batch 2).

Produktionierte Konvergenz der erprobten QC-Gates aus ``fal_clip_pipeline.py``
(Video-QC vor Annahme) und ``agnes_clip_qc.py`` (Nachlauf-Report): Pro Clip
werden N Frames gleichmäßig gesampelt und per **kostenlosem** Agnes-multimodal-
Chat gegen eine generische Rubrik geprüft (Renderfehler wie Schwarz-/Flimmern-
Frames, schmelzende Gesichter, gedrehtes Bild — deckt den dokumentierten
v2.5-Vertikalbild-Defekt, Wasser-/Text-Artefakte, Prompt-Kontrakt). Das Gate
kostet daher keinen Cent und läuft auf der gratis Agnes-Strecke genauso wie
bei bezahlten Providern.

Grundsätze (aus den Experimenten übernommen):
    - **Fail-open**: QC-Fehler (kein ffmpeg, Chat-Ausfall, leere Antwort) werden
      als PASS mit Begründung gewertet und geloggt — die Prüfung darf den
      Pipeline-Lauf nie zum Scheitern bringen; auffällige Clips landen im
      ``qc_report`` des Task-States zur manuellen Nachsicht.
    - **Eine Regenerierungs-Chance**: die Regenerierungs-Loop lebt in der
      Pipeline (``MultiScenePipeline._run_scene_qc``), das Gate selbst ist
      zustandsfrei und urteilt nur.
    - Antworten des VLM: erste Zeile ``PASS - ...`` / ``FAIL - <Grund>``.
"""

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from core.compositor.ffmpeg_tool import resolve_ffmpeg, resolve_ffprobe

logger = logging.getLogger(__name__)

# Sample-Frames in Prozent des Clips (chronologisch; Deckung Anfang/Mitte/Ende)
_QC_FRAME_FRACTIONS = (0.1, 0.3, 0.5, 0.7, 0.9)

# Generische Rubrik: nur harte, objective Render-/Inhaltsfehler — kein
# Projekt-spezifischer Stilzwang (die Experiment-Rubriken waren music-video-
# spezifisch; hier bewusst allgemeingültig für alle 6 Task-Typen).
_QC_SYSTEM_PROMPT = (
    "You are a strict AI-video quality supervisor. You are shown several frames "
    "sampled in chronological order from ONE generated video clip, plus the "
    "prompt the clip was generated from. Answer with EXACTLY ONE line: "
    "'PASS - <one short sentence>' or 'FAIL - <reason, mention the frame number>'. "
    "FAIL if ANY frame shows: "
    "(1) a broken render: fully black, grey or solid-color frames, heavy noise, "
    "tile or compression artefacts, smeared or duplicated ghosting; "
    "(2) a badly deformed, melting or duplicated face/body — only when a person "
    "or character is actually visible in that frame; "
    "(3) the whole picture rotated sideways or upside down; "
    "(4) an overlaid watermark, logo, UI chrome or garbled pseudo-text; "
    "(5) content that clearly contradicts the clip prompt (a completely "
    "different subject or setting). "
    "Do NOT fail for: artistic style choices, motion blur, brief transition "
    "frames, shots without people, or minor imperfections. Judge now."
)


@dataclass(frozen=True)
class QCVerdict:
    """Ergebnis eines Clip-QC-Checks (``passed`` = annehmen)."""

    passed: bool
    reason: str = ""
    frames: int = 0


# Kontaktbogen-Anteile: Anfang, Mitte, Ende des Clips (menschliche Sichtprüfung).
_CONTACT_SHEET_FRACTIONS = (0.25, 0.50, 0.75)


def build_contact_sheet(
    video_path: str,
    out_path: Optional[str] = None,
    fractions: tuple = _CONTACT_SHEET_FRACTIONS,
) -> Optional[str]:
    """Baut ein Kontaktblatt aus Frames bei 25/50/75 % der Clip-Laufzeit (hstack).

    Gegenstück zum VLM-Gate derselben Datei: Das Gate urteilt automatisiert, das
    Kontaktblatt macht dieselbe Stelle für den Menschen prüfbar (铁律: 单段确认流程,
    Keyframes bei 25/50/75 %). Läuft **fail-open** — fehlt ffmpeg oder scheitert ein
    Frame, wird ``None`` zurückgegeben und der Pipelinelauf nie abgebrochen.

    Args:
        video_path: Pfad zum Clip.
        out_path: Ziel-PNG; Default ``<clip_stem>_qa_trio.png`` neben dem Clip.
        fractions: Zu sampelnde Laufzeitanteile in chronologischer Reihenfolge.

    Returns:
        Pfad des erzeugten Kontaktblatts oder ``None``.
    """
    ffmpeg = resolve_ffmpeg()
    ffprobe = resolve_ffprobe()
    if not ffmpeg or not ffprobe or not os.path.isfile(video_path):
        return None

    stem, _ = os.path.splitext(video_path)
    target = out_path or f"{stem}_qa_trio.png"

    try:
        probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=30, check=True,
        )
        duration = float(probe.stdout.strip().splitlines()[0])
    except Exception as e:
        logger.warning("[QC] contact sheet: ffprobe failed (%s)", e)
        return None
    if duration <= 0:
        return None

    frames: list = []
    try:
        for frac in fractions:
            pct = int(round(frac * 100))
            frame_path = f"{stem}_qa{pct:02d}.png"
            subprocess.run(
                [ffmpeg, "-y", "-v", "error",
                 "-ss", f"{duration * frac:.2f}", "-i", video_path,
                 "-frames:v", "1", frame_path],
                stdin=subprocess.DEVNULL, capture_output=True,
                check=True, timeout=60,
            )
            if os.path.isfile(frame_path) and os.path.getsize(frame_path) > 0:
                frames.append(frame_path)
        if len(frames) < 2:
            logger.warning("[QC] contact sheet: only %d/%d frames extracted", len(frames), len(fractions))
            return None

        inputs = []
        for f in frames:
            inputs += ["-i", f]
        stack = "".join(f"[{i}:v]" for i in range(len(frames)))
        filter_complex = f"{stack}hstack=inputs={len(frames)}[v]"
        subprocess.run(
            [ffmpeg, "-y", "-v", "error", *inputs,
             "-filter_complex", filter_complex, "-map", "[v]", target],
            stdin=subprocess.DEVNULL, capture_output=True,
            check=True, timeout=120,
        )
    except Exception as e:
        logger.warning("[QC] contact sheet build failed: %s", e)
        return None
    finally:
        for f in frames:
            try:
                os.remove(f)
            except OSError:
                pass

    if os.path.isfile(target) and os.path.getsize(target) > 0:
        return target
    return None


class ClipQCGate:
    """Zustandsfreies VLM-Qualitätsgate für einzelne Videoclips.

    Args:
        chat_api: ``AgnesChatAPI``-Instanz (multimodal); wird von der Pipeline
            call-time gebaut, damit Mock-Patches greifen.
        frame_fractions: Sample-Positionen (Anteil der Clip-Dauer).
    """

    def __init__(
        self,
        chat_api,
        frame_fractions: tuple = _QC_FRAME_FRACTIONS,
    ):
        self.chat = chat_api
        self.frame_fractions = tuple(frame_fractions)

    # ── Frame-Sampling ───────────────────────────────────────────

    def _probe_duration(self, video_path: str) -> float:
        """Clip-Dauer via ffprobe lesen; Fallbacks: moviepy, dann 10 s Schätzung."""
        ffprobe = resolve_ffprobe()
        if ffprobe:
            try:
                out = subprocess.run(
                    [ffprobe, "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                    capture_output=True, text=True, timeout=30, check=True,
                )
                return float(out.stdout.strip().splitlines()[0])
            except Exception as e:
                logger.debug("[QC] ffprobe duration failed (%s), falling back", e)
        try:
            from moviepy import VideoFileClip

            with VideoFileClip(video_path) as clip:
                return float(clip.duration or 0) or 10.0
        except Exception as e:
            logger.debug("[QC] moviepy duration failed (%s), using 10s guess", e)
            return 10.0

    def _extract_frames(self, video_path: str, out_dir: str) -> list:
        """N Frames gleichmäßig sampeln → Liste lokaler JPG-Pfade (ggf. leer)."""
        ffmpeg = resolve_ffmpeg()
        if not ffmpeg:
            logger.warning("[QC] ffmpeg not found — QC skipped (fail-open)")
            return []
        os.makedirs(out_dir, exist_ok=True)
        duration = self._probe_duration(video_path)
        frames: list = []
        for frac in self.frame_fractions:
            pct = int(frac * 100)
            out_path = os.path.join(out_dir, f"qc_{pct:02d}.jpg")
            try:
                subprocess.run(
                    [ffmpeg, "-y", "-v", "error",
                     "-ss", f"{max(duration * frac, 0):.2f}",
                     "-i", video_path,
                     "-frames:v", "1", out_path],
                    stdin=subprocess.DEVNULL, capture_output=True,
                    check=True, timeout=60,
                )
                if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                    frames.append(out_path)
            except Exception as e:
                logger.warning("[QC] frame extract failed at %d%%: %s", pct, e)
        return frames

    # ── Urteil ───────────────────────────────────────────────────

    def _judge_sync(self, video_path: str, prompt: str, frames: list) -> str:
        """Chat-Aufruf (blockierend; von ``judge_clip`` in einen Thread verschoben)."""
        user = (
            f"Clip prompt: {(prompt or '').strip()[:800] or '(none)'}\n\n"
            f"The {len(frames)} frames above are chronological samples of one "
            "generated clip. Judge now."
        )
        return (self.chat.chat_multimodal(_QC_SYSTEM_PROMPT, user, frames) or "").strip()

    def _deterministic_frame_checks(self, frames: list) -> Optional[QCVerdict]:

        """Schnelle lokale Heuristiken (Schwarzbild / Frozen Frame) vor dem VLM-Aufruf."""
        if not frames:
            return None
        try:
            from PIL import Image, ImageStat, ImageChops

            images = []
            for f in frames:
                try:
                    img = Image.open(f).convert("RGB")
                    images.append(img)
                except Exception:
                    return None

            if not images:
                return None

            # 1. Black-Frame-Erkennung: Sind alle Frames komplett schwarz?
            all_black = True
            for img in images:
                stat = ImageStat.Stat(img)
                mean_brightness = sum(stat.mean) / len(stat.mean)
                if mean_brightness >= 5.0:
                    all_black = False
                    break
            if all_black:
                return QCVerdict(
                    passed=False,
                    reason="FAIL - deterministic check: all sampled frames are completely black (mean brightness < 5.0)",
                    frames=len(frames)
                )

            # 2. Frozen-Frame-Erkennung: Sind mehrere Frames zu 100% identisch?
            if len(images) >= 3:
                all_identical = True
                first_img = images[0]
                for other_img in images[1:]:
                    diff = ImageChops.difference(first_img, other_img)
                    stat = ImageStat.Stat(diff)
                    mean_diff = sum(stat.mean) / len(stat.mean)
                    if mean_diff > 0.5:
                        all_identical = False
                        break
                if all_identical:
                    return QCVerdict(
                        passed=False,
                        reason="FAIL - deterministic check: video motion is frozen/static across all sampled frames",
                        frames=len(frames)
                    )

        except Exception as e:
            logger.debug("[QC] deterministic check skipped: %s", e)
            return None

        return None

    async def judge_clip(self, video_path: str, prompt: str) -> QCVerdict:
        """Einen gespeicherten Clip beurteilen — fail-open, wirft nie."""
        try:
            out_dir = os.path.join(os.path.dirname(video_path), "qc_frames")
            frames = await asyncio.to_thread(self._extract_frames, video_path, out_dir)
            if not frames:
                return QCVerdict(
                    passed=True,
                    reason="no QC frames extractable — manual review advised (fail-open)",
                )

            # Schneller lokaler Check vor teurem VLM-Aufruf
            fast_check = await asyncio.to_thread(self._deterministic_frame_checks, frames)
            if fast_check is not None:
                return fast_check

            raw = await asyncio.to_thread(self._judge_sync, video_path, prompt, frames)
            first_line = raw.splitlines()[0].strip() if raw else ""

            if not first_line:
                return QCVerdict(
                    passed=True,
                    reason="empty VLM verdict — manual review advised (fail-open)",
                    frames=len(frames),
                )
            passed = first_line.upper().startswith("PASS")
            return QCVerdict(passed=passed, reason=first_line[:300], frames=len(frames))
        except Exception as e:
            logger.warning("[QC] judge_clip failed (fail-open PASS): %s", e)
            return QCVerdict(passed=True, reason=f"qc error (fail-open): {e}")
