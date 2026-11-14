"""scripts/assemble_master_video.py
Финальная сборка полного музыкального клипа
«Метаморфоза материи: Бумага, Пепел и Свет» (Шоты 01-36).
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MasterAssembly")

OUTPUT_DIR = Path("output").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
AUDIO_FILE = Path("uploaded_media_1793789661300.mp3").resolve()
FINAL_MV = OUTPUT_DIR / "metamorfoza_materii_final_full_mv.mp4"

ORDERED_SHOTS = [
    OUTPUT_DIR / "metamorfoza_materii_master_23_shots.mp4",
    OUTPUT_DIR / "shot_24_infinite_freedom.mp4",
    OUTPUT_DIR / "shot_25_paper_wall.mp4",
    OUTPUT_DIR / "shot_26_gravity_crumble.mp4",
    OUTPUT_DIR / "shot_27_mirror_reflections.mp4",
    OUTPUT_DIR / "shot_28_peeling_scenery.mp4",
    OUTPUT_DIR / "shot_29_stepping_to_light.mp4",
    OUTPUT_DIR / "shot_30_decisive_eyes.mp4",
    OUTPUT_DIR / "shot_31_walls_crumble_to_dust.mp4",
    OUTPUT_DIR / "shot_32_step_onto_pier.mp4",
    OUTPUT_DIR / "shot_33_lake_dawn_panorama.mp4",
    OUTPUT_DIR / "shot_34_deep_breath_freedom.mp4",
    OUTPUT_DIR / "shot_35_dewdrops_wildflowers.mp4",
    OUTPUT_DIR / "shot_36_grand_finale_sunrise.mp4",
]

def main():
    logger.info("🎬 НАЧАЛО СБОРКИ ФИНАЛЬНОГО МАСТЕР-ВИДЕОКЛИПА...")

    # Проверка наличия всех файлов
    missing = [str(f) for f in ORDERED_SHOTS if not f.exists()]
    if missing:
        logger.error(f"❌ Отсутствуют файлы: {missing}")
        sys.exit(1)

    if not AUDIO_FILE.exists():
        logger.error(f"❌ Аудиотрек не найден: {AUDIO_FILE}")
        sys.exit(1)

    # 1. Нормализация и склейка всех видеорядов в единый файл
    # Сформируем список для concat demuxer
    concat_list = OUTPUT_DIR / "master_concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for shot in ORDERED_SHOTS:
            f.write(f"file '{shot.resolve()}'\n")

    temp_video = OUTPUT_DIR / "temp_master_video_all_36.mp4"

    logger.info("1. Склейка видеоряда (36 шотов) с нормализацией до 1280x720, 24fps...")
    cmd_video = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
        "-an",
        str(temp_video)
    ]
    subprocess.run(cmd_video, check=True)

    # 2. Наложение оригинального мастер-аудиотрека
    logger.info("2. Наложение оригинального мастер-аудиотрека («Метаморфоза материи: Бумага, Пепел и Свет»)...")
    cmd_mux = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(AUDIO_FILE),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        str(FINAL_MV)
    ]
    subprocess.run(cmd_mux, check=True)

    # 3. Извлечение финальных метаданных
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size,bit_rate:stream=width,height,codec_name", "-of", "json", str(FINAL_MV)],
        capture_output=True, text=True, check=True
    )
    meta = json.loads(probe.stdout)

    # 4. Копирование в brain
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(FINAL_MV), BRAIN_DIR / FINAL_MV.name)

    # Создание финального постера / титульного кадра
    poster_jpg = OUTPUT_DIR / "metamorfoza_materii_final_poster.jpg"
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", "00:03:35",
        "-i", str(FINAL_MV),
        "-vframes", "1", "-q:v", "2",
        str(poster_jpg)
    ], check=True)
    shutil.copy2(str(poster_jpg), BRAIN_DIR / poster_jpg.name)

    logger.info("============================================================")
    logger.info("🎉🎉 ПОЛНЫЙ ФИЛЬМ УСПЕШНО СОЗДАН И СОХРАНЁН! 🎉🎉")
    logger.info(f"Файл: {FINAL_MV}")
    logger.info(f"Длительность: {meta['format'].get('duration')} сек")
    logger.info(f"Размер: {int(meta['format'].get('size')) / 1024 / 1024:.2f} МБ")
    logger.info("============================================================")

if __name__ == '__main__':
    main()
