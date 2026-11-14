# -*- coding: utf-8 -*-
"""pipeline_nikogda.py — Режиссёрский пайплайн сборки музыкального клипа «Никогда не боюсь» (146.04 сек).

Поддерживает:
1. Автоматическую сборку видеоклипа с плавными кинематографическими движениями камеры (Ken Burns)
   по ключевым кадрам 16:9 (scene_01.png ... scene_18.png).
2. Подхват сгенерированных видеороликов из Google Flow (clips/scene_XX.mp4).
3. Синхронизацию каждого кадра с музыкальными тактами, куплетами и припевами трека song.mp3.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("NikogdaPipeline")

FRAMES_DIR = Path(__file__).resolve().parent
CLIPS_DIR = FRAMES_DIR / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
SONG = FRAMES_DIR / "song.mp3"

SCENES = [
    {"id": "01", "dur": 6.00, "name": "Рампа самолёта на 4000 м", "motion": "zoom_in"},
    {"id": "02", "dur": 7.00, "name": "Свободное падение на закате (👍)", "motion": "pan_down"},
    {"id": "03", "dur": 7.00, "name": "Долина тысячи змей", "motion": "pan_up"},
    {"id": "04", "dur": 7.00, "name": "Берег сотни крокодилов", "motion": "pan_right"},
    {"id": "05", "dur": 8.00, "name": "Рой шершней в джунглях", "motion": "zoom_in"},
    {"id": "06", "dur": 8.00, "name": "Кромка извергающегося вулкана", "motion": "pan_left"},
    {"id": "07", "dur": 8.00, "name": "Эпицентр торнадо F5", "motion": "zoom_in"},
    {"id": "08", "dur": 8.00, "name": "Вингсьют в скальном ущелье", "motion": "pan_down"},
    {"id": "09", "dur": 7.00, "name": "Огненный взрыв моста в слоу-мо", "motion": "zoom_out"},
    {"id": "10", "dur": 8.00, "name": "Стена огня: триумф «НИКОГДА!»", "motion": "zoom_in"},
    {"id": "11", "dur": 7.00, "name": "Утренняя пробежка сквозь зомби", "motion": "pan_right"},
    {"id": "12", "dur": 7.00, "name": "Один против бегущей толпы", "motion": "zoom_in"},
    {"id": "13", "dur": 6.00, "name": "Рука помощи упавшему", "motion": "pan_up"},
    {"id": "14", "dur": 5.00, "name": "«Мы сильнее всех!»: сплочение", "motion": "zoom_out"},
    {"id": "15", "dur": 8.00, "name": "Скачка сквозь песчаную бурю", "motion": "pan_left"},
    {"id": "16", "dur": 8.00, "name": "15-метровый шторм в море", "motion": "zoom_in"},
    {"id": "17", "dur": 14.00, "name": "Вершина мира над облаками", "motion": "pan_right"},
    {"id": "18", "dur": 17.04, "name": "Вспышки победы и Рассветная дорога", "motion": "zoom_out"},
]

def build_motion_clip(img_path: Path, out_path: Path, duration: float, motion: str):
    """Генерирует плавный видеофрагмент 1080p (24fps) из статичного кадра 16:9 с кинематографическим движением."""
    fps = 24
    frames = int(duration * fps)
    
    # Фильтры движения Ken Burns
    if motion == "zoom_in":
        vf = f"zoompan=z='min(zoom+0.0015,1.25)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"
    elif motion == "zoom_out":
        vf = f"zoompan=z='if(lte(zoom,1.0),1.25,max(1.001,zoom-0.0015))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"
    elif motion == "pan_right":
        vf = f"zoompan=z=1.15:x='if(lte(on,1),0,x+1)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif motion == "pan_left":
        vf = f"zoompan=z=1.15:x='if(lte(on,1),iw*0.15,x-1)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif motion == "pan_down":
        vf = f"zoompan=z=1.15:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,y+0.8)':d={frames}:s=1920x1080:fps={fps}"
    else:  # pan_up
        vf = f"zoompan=z=1.15:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),ih*0.15,y-0.8)':d={frames}:s=1920x1080:fps={fps}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img_path),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        "-an", str(out_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def assemble_clip():
    logger.info("=== Запуск сборки музыкального клипа «Никогда не боюсь» ===")
    concat_list = CLIPS_DIR / "concat_list.txt"
    entries = []

    for sc in SCENES:
        sc_id = sc["id"]
        dur = sc["dur"]
        name = sc["name"]
        motion = sc["motion"]

        # 1. Проверяем наличие готового видео из Google Flow
        video_candidate = CLIPS_DIR / f"scene_{sc_id}.mp4"
        if video_candidate.exists() and video_candidate.stat().st_size > 50000:
            logger.info(f"Сцена {sc_id} [{name}]: Найдено сгенерированное видео Flow!")
            prepared_mp4 = CLIPS_DIR / f"prep_{sc_id}.mp4"
            cmd_scale = [
                "ffmpeg", "-y", "-i", str(video_candidate),
                "-t", str(dur),
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-an", str(prepared_mp4)
            ]
            subprocess.run(cmd_scale, check=True, capture_output=True)
            entries.append(f"file '{prepared_mp4.resolve().as_posix()}'")
            continue

        # 2. Иначе используем референсный кадр 16:9 с кинематографическим движением
        img_path = FRAMES_DIR / f"scene_{sc_id}.png"
        if not img_path.exists():
            logger.error(f"Кадр {img_path} не найден!")
            continue

        prep_clip = CLIPS_DIR / f"prep_{sc_id}.mp4"
        logger.info(f"Сцена {sc_id} [{name}]: Рендер движения ({dur}с, {motion})...")
        build_motion_clip(img_path, prep_clip, dur, motion)
        entries.append(f"file '{prep_clip.resolve().as_posix()}'")

    with open(concat_list, "w", encoding="utf-8") as f:
        f.write("\n".join(entries) + "\n")

    final_output = FRAMES_DIR / "Никогда_не_боюсь_клип.mp4"
    logger.info(f"Финальная сборка с песней в: {final_output}")

    cmd_final = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-i", str(SONG),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", str(final_output)
    ]
    subprocess.run(cmd_final, check=True, capture_output=True)
    logger.info(f"ГОТОВО! Клип успешно собран: {final_output} ({final_output.stat().st_size} байт)")
    return final_output

if __name__ == "__main__":
    assemble_clip()
