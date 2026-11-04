"""core.audio.subtitle.remotion_renderer — Декларативный рендеринг субтитров через Remotion.

Превращает субтитры (.srt или cues) в современный кинематографичный оверлей с подсветкой текущих слов
и плавной анимацией на базе React/Remotion, объединяя его с видео через FFmpeg overlay.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from core.compositor.ffmpeg_tool import resolve_binary

logger = logging.getLogger(__name__)

REMOTION_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "remotion_subtitles")
)


class RemotionSubtitleRenderer:
    """Модуль интеграции декларативных React-субтитров через Remotion."""

    @classmethod
    def is_available(cls) -> bool:
        """Проверяет доступность Node.js и установку Remotion пакетов."""
        node_bin = shutil.which("node")
        if not node_bin:
            return False
        # Проверяем наличие render.mjs и node_modules
        render_script = os.path.join(REMOTION_DIR, "render.mjs")
        nm_dir = os.path.join(REMOTION_DIR, "node_modules", "@remotion", "renderer")
        return os.path.exists(render_script) and os.path.exists(nm_dir)

    @staticmethod
    def parse_srt(srt_path: str) -> List[Dict[str, Any]]:
        """Парсит стандартный .srt файл в структурированный список для Remotion."""
        if not os.path.exists(srt_path):
            return []

        with open(srt_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        def srt_time_to_seconds(t_str: str) -> float:
            # "00:01:23,456" -> seconds
            t_str = t_str.strip().replace(",", ".")
            parts = t_str.split(":")
            if len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
            return float(parts[0])

        pattern = r"(\d+)\r?\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\r?\n(.*?)(?=\r?\n\r?\n|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)

        items = []
        for idx, start_str, end_str, text_str in matches:
            cleaned_text = re.sub(r"<[^>]+>", "", text_str).strip()
            cleaned_text = " ".join(cleaned_text.split())
            if not cleaned_text:
                continue
            start_sec = srt_time_to_seconds(start_str)
            end_sec = srt_time_to_seconds(end_str)
            items.append({
                "id": int(idx),
                "start": start_sec,
                "end": end_sec,
                "text": cleaned_text,
            })
        return items

    @classmethod
    async def render_and_overlay(
        cls,
        base_video_path: str,
        srt_path: str,
        output_path: str,
        video_width: int = 768,
        video_height: int = 1344,
        style: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Рендерит анимированные субтитры через Remotion и накладывает их на видео.

        Args:
            base_video_path: Путь к исходному видео
            srt_path: Путь к .srt файлу
            output_path: Путь для сохранения итогового видео
            video_width: Ширина видео
            video_height: Высота видео
            style: Параметры стиля (fontSize, highlightColor, textColor и др.)

        Returns:
            Путь к output_path

        Raises:
            RuntimeError: Если Remotion недоступен или рендеринг завершился ошибкой
        """
        if not cls.is_available():
            raise RuntimeError(
                "[RemotionSubtitles] Remotion dependencies not ready. Run 'npm install' in remotion_subtitles/"
            )

        subtitles = cls.parse_srt(srt_path)
        if not subtitles:
            logger.info("[RemotionSubtitles] No subtitles found to render, copying base video")
            shutil.copy2(base_video_path, output_path)
            return output_path

        # Определение длительности видео через ffprobe
        ffprobe = resolve_binary("ffprobe") or "ffprobe"
        duration_cmd = [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            base_video_path
        ]
        loop = asyncio.get_event_loop()

        def _get_dur():
            res = subprocess.run(duration_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            try:
                return float(res.stdout.strip())
            except Exception:
                return subtitles[-1]["end"] + 1.0

        duration_sec = await loop.run_in_executor(None, _get_dur)

        work_dir = os.path.dirname(output_path) or "."
        props_path = os.path.join(work_dir, "remotion_props.json")
        overlay_mov_path = os.path.join(work_dir, "subtitles_overlay.mov")

        props_payload = {
            "subtitles": subtitles,
            "style": style or {
                "fontSize": max(int(video_width * 0.045), 24),
                "highlightColor": "#FBBF24",
                "textColor": "#FFFFFF",
                "positionY": "82%",
            },
        }

        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props_payload, f, ensure_ascii=False, indent=2)

        # 1. Рендеринг прозрачного MOV через Node CLI
        node_bin = shutil.which("node") or "node"
        render_script = os.path.join(REMOTION_DIR, "render.mjs")
        render_cmd = [
            node_bin, render_script,
            "--props", props_path,
            "--output", overlay_mov_path,
            "--width", str(video_width),
            "--height", str(video_height),
            "--duration", f"{duration_sec:.2f}",
            "--fps", "30",
        ]

        logger.info(f"[RemotionSubtitles] Rendering overlay via Remotion CLI ({duration_sec:.2f}s)...")
        render_proc = await asyncio.create_subprocess_exec(
            *render_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=REMOTION_DIR,
        )
        stdout, stderr = await render_proc.communicate()

        if render_proc.returncode != 0:
            err_msg = stderr.decode(errors="replace")[:400]
            logger.error(f"[RemotionSubtitles] Remotion render failed: {err_msg}")
            raise RuntimeError(f"Remotion render failed: {err_msg}")

        # 2. Быстрое слияние через FFmpeg overlay
        ffmpeg = resolve_binary("ffmpeg") or "ffmpeg"
        ffmpeg_cmd = [
            ffmpeg, "-y",
            "-i", base_video_path,
            "-i", overlay_mov_path,
            "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
            "-map", "[v]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-c:a", "copy",
            output_path,
        ]

        logger.info("[RemotionSubtitles] Merging overlay with video via FFmpeg...")
        merge_proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, merge_err = await merge_proc.communicate()

        # Очистка временных файлов
        for p in (props_path, overlay_mov_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

        if merge_proc.returncode != 0:
            err_msg = merge_err.decode(errors="replace")[:400]
            raise RuntimeError(f"FFmpeg subtitle merge failed: {err_msg}")

        logger.info(f"[RemotionSubtitles] ✅ Successfully composited Remotion subtitles to: {output_path}")
        return output_path
