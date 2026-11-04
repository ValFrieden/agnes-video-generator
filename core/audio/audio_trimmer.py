"""core.audio.audio_trimmer — Модуль точной нарезки и кадрирования аудиофрагментов.

Использует FFmpeg для мгновенного среза нужного сегмента без потерь или с перекодированием
в студийный битрейт (320 kbps). Позволяет подготовить короткий фрагмент для музыкального видео
или зацикленного клипа из длинного трека.
"""

import logging
import os
import subprocess
from typing import Optional

from core.compositor.ffmpeg_tool import probe_duration, resolve_binary

logger = logging.getLogger(__name__)


def trim_audio_segment(
    input_path: str,
    output_path: str,
    start_sec: float,
    end_sec: float,
    bitrate: str = "320k",
) -> float:
    """Вырезает отрезок аудиофайла от start_sec до end_sec.

    Args:
        input_path: Путь к исходному аудиофайлу.
        output_path: Путь для сохранения результата.
        start_sec: Начальная секунда (>= 0).
        end_sec: Конечная секунда (> start_sec).
        bitrate: Битрейт аудио (по умолчанию 320k для максимального качества).

    Returns:
        Фактическая длительность результирующего фрагмента в секундах.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Исходный аудиофайл не найден: {input_path}")

    start_sec = max(0.0, float(start_sec))
    end_sec = float(end_sec)
    if end_sec <= start_sec:
        raise ValueError(
            f"Некорректный интервал обрезки: start_sec ({start_sec}) должен быть меньше end_sec ({end_sec})."
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    ffmpeg_bin = resolve_binary("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        f"{start_sec:.3f}",
        "-to",
        f"{end_sec:.3f}",
        "-i",
        input_path,
        "-c:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        output_path,
    ]

    logger.info(
        f"[AudioTrimmer] Cutting segment [{start_sec:.2f}s -> {end_sec:.2f}s] "
        f"from {os.path.basename(input_path)} -> {os.path.basename(output_path)}"
    )

    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        err = res.stderr[-300:] if res.stderr else "Unknown error"
        raise RuntimeError(f"FFmpeg audio trim failed (code {res.returncode}): {err}")

    actual_dur = probe_duration(output_path)
    if not actual_dur or actual_dur <= 0.0:
        actual_dur = end_sec - start_sec

    logger.info(f"[AudioTrimmer] Done trimming: {output_path} (duration={actual_dur:.2f}s)")
    return actual_dur
