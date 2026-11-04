"""core.compositor.post_processor — Optionaler Video-Post-Prozessor (auto-editor Integration)

Entfernt Stille, Dead Air und schlechte Frames aus fertig zusammengesetzten Videos.
Konfiguration via Umgebungsvariable AGNES_POST_PROCESS=1 (Standard: aus).

Verwendung:
    # Direkt (synchron, z.B. in ThreadPool):
    from core.compositor.post_processor import post_process_video
    video_path = post_process_video(video_path)  # in-place, graceful degradation

    # Async-Wrapper für Pipelines:
    from core.compositor.post_processor import remove_silence_async
    await remove_silence_async(input_path, output_path)

Umgebungsvariablen:
    AGNES_POST_PROCESS=1          Aktiviert Post-Processing (Standard: aus)
    AGNES_PP_THRESHOLD=4%         Audio-Schwellwert (Standard: 4%)
    AGNES_PP_MARGIN=0.2sec        Randbereich um Stille (Standard: 0.2sec)
"""
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


def is_post_processing_enabled() -> bool:
    """Gibt True zurück wenn AGNES_POST_PROCESS=1 gesetzt ist."""
    return os.environ.get("AGNES_POST_PROCESS", "0").strip() == "1"


def remove_silence(
    input_path: str,
    output_path: str,
    audio_threshold: str = "4%",
    margin: str = "0.2sec",
) -> str:
    """Entfernt Stille aus einem Video via auto-editor (synchron).

    Args:
        input_path: Eingabevideo-Pfad
        output_path: Ausgabevideo-Pfad
        audio_threshold: Lautstärke-Schwellwert (z.B. "4%")
        margin: Randbereich um Stille (z.B. "0.2sec")

    Returns:
        output_path bei Erfolg

    Raises:
        RuntimeError: Wenn auto-editor nicht verfügbar oder Verarbeitung fehlschlägt.
    """
    try:
        import auto_editor  # noqa: F401 — verfügbarkeits-check
    except ImportError:
        raise RuntimeError(
            "[PostProcessor] auto-editor ist nicht installiert. "
            "Installieren mit: pip install auto-editor"
        )

    logger.info(
        f"[PostProcessor] Entferne Stille aus {os.path.basename(input_path)} "
        f"(threshold={audio_threshold}, margin={margin})"
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # auto-editor schreibt direkt in output; temporäres Verzeichnis für Zwischenprodukte
    with tempfile.TemporaryDirectory(prefix="agnes_autoeditor_") as tmp_dir:
        cmd = [
            "auto-editor",
            input_path,
            "--output", output_path,
            "--edit", f"audio:threshold={audio_threshold}",
            "--margin", margin,
            "--no-open",
            "--temp-dir", tmp_dir,
        ]
        logger.debug(f"[PostProcessor] cmd: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 Minuten max
        )

    if result.returncode != 0:
        logger.error(f"[PostProcessor] auto-editor Fehler: {result.stderr[:500]}")
        raise RuntimeError(
            f"[PostProcessor] auto-editor fehlgeschlagen (code {result.returncode}): "
            f"{result.stderr[:200]}"
        )

    logger.info(f"[PostProcessor] Stille entfernt → {os.path.basename(output_path)}")
    return output_path


async def remove_silence_async(
    input_path: str,
    output_path: str,
    audio_threshold: str = "4%",
    margin: str = "0.2sec",
) -> str:
    """Async-Wrapper um remove_silence() — läuft in ThreadPool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: remove_silence(input_path, output_path, audio_threshold, margin),
    )


def post_process_video(input_path: str, output_path: Optional[str] = None) -> str:
    """Wendet alle aktivierten Post-Processing-Schritte auf ein Video an.

    Wenn output_path None ist, wird input_path in-place überschrieben.

    Args:
        input_path: Eingabevideo
        output_path: Ausgabevideo (None = in-place)

    Returns:
        Pfad zum verarbeiteten Video
    """
    if not is_post_processing_enabled():
        logger.debug("[PostProcessor] Post-Processing deaktiviert (AGNES_POST_PROCESS!=1)")
        return input_path

    inplace = output_path is None
    if inplace:
        # In-place: temporäre Zwischendatei
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_postprocessed{ext}"

    try:
        remove_silence(input_path, output_path)
        if inplace:
            # Ersetze Original mit verarbeitetem Video
            shutil.move(output_path, input_path)
            return input_path
        return output_path
    except RuntimeError as e:
        logger.warning(f"[PostProcessor] Überspringe Post-Processing: {e}")
        # Graceful degradation: Original zurückgeben
        if inplace and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        return input_path


async def post_process_video_async(input_path: str, output_path: Optional[str] = None) -> str:
    """Async-Wrapper um post_process_video — führt die Stille-Entfernung
    in einem ThreadPool aus, damit der FastAPI-Haupt-Thread / Event-Loop nicht blockiert."""
    if not is_post_processing_enabled():
        return input_path
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: post_process_video(input_path, output_path),
    )

