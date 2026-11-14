"""scripts/update_shot_01_and_rebuild.py
Замена старого Шота 01 (с резным собором) на новый Шот 01
(со складыванием в домик-куб из Шота 02) и финальная пересборка клипа.
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
logger = logging.getLogger("UpdateShot01")

OUTPUT_DIR = Path("output").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
AUDIO_FILE = Path("uploaded_media_1793789661300.mp3").resolve()
FINAL_MV = OUTPUT_DIR / "metamorfoza_materii_final_full_mv.mp4"

NEW_SHOT_01_SOURCE = OUTPUT_DIR / "shot_01_single_panel_new.mp4"
OLD_SHOT_01 = OUTPUT_DIR / "shot_01_single_panel.mp4"
BACKUP_OLD_SHOT_01 = OUTPUT_DIR / "shot_01_single_panel_old_cathedral.mp4"

ACT_01_SHOTS = [
    OUTPUT_DIR / "shot_01_single_panel.mp4",
    OUTPUT_DIR / "shot_02_room_cube.mp4",
    OUTPUT_DIR / "shot_03_sealed_cube.mp4",
    OUTPUT_DIR / "shot_04_light_burst.mp4",
]

def main():
    logger.info("🎬 Замена Шота 01 на новый и пересборка клипа...")

    # 1. Бэкап старого Шота 01
    if OLD_SHOT_01.exists() and not BACKUP_OLD_SHOT_01.exists():
        shutil.copy2(str(OLD_SHOT_01), str(BACKUP_OLD_SHOT_01))
        logger.info(f"Бэкап старого Шота 01 сохранен: {BACKUP_OLD_SHOT_01.name}")

    # 2. Обрезка нового Шота 01 ровно до 5.041667 сек для точного тайминга Акта 01
    logger.info("Обрезка нового Шота 01 под тайминг 5.041667 сек...")
    temp_shot_01 = OUTPUT_DIR / "temp_shot_01_trimmed.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(NEW_SHOT_01_SOURCE),
        "-t", "5.041667",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
        "-an",
        str(temp_shot_01)
    ], check=True)

    shutil.move(str(temp_shot_01), str(OLD_SHOT_01))
    logger.info("✅ Новый Шот 01 установлен на место shot_01_single_panel.mp4!")

    # 3. Пересборка Акта 01 (Шоты 01, 02, 03, 04)
    logger.info("Пересборка Акта 01 (Шоты 01-04)...")
    act_01_concat = OUTPUT_DIR / "concat_act_01.txt"
    with open(act_01_concat, "w", encoding="utf-8") as f:
        for s in ACT_01_SHOTS:
            f.write(f"file '{s.resolve()}'\n")

    act_01_output = OUTPUT_DIR / "act_01_assembled.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(act_01_concat),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        "-an",
        str(act_01_output)
    ], check=True)
    logger.info("✅ Акт 01 успешно пересобран!")

    # 4. Пересборка metamorfoza_materii_master_23_shots.mp4
    # Акт 01 (1-4) + Акт 02 (5-9) + Акт 03 (10-16) + Акт 04 (17-23)
    logger.info("Пересборка блока Шотов 01-23...")
    master_acts = [
        OUTPUT_DIR / "act_01_assembled.mp4",
        OUTPUT_DIR / "act_02_assembled.mp4",
        OUTPUT_DIR / "act_03_assembled.mp4",
        OUTPUT_DIR / "act_04_assembled.mp4",
    ]
    acts_concat = OUTPUT_DIR / "master_acts_concat_list.txt"
    with open(acts_concat, "w", encoding="utf-8") as f:
        for a in master_acts:
            f.write(f"file '{a.resolve()}'\n")

    master_23_output = OUTPUT_DIR / "metamorfoza_materii_master_23_shots.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(acts_concat),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        "-an",
        str(master_23_output)
    ], check=True)
    logger.info("✅ Блок Шотов 01-23 успешно обновлен!")

    # 5. Финальная склейка всех 36 шотов с оригинальным аудио
    logger.info("Финальная склейка всех 36 шотов с оригинальным мастер-аудио...")
    ordered_shots = [
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

    master_concat = OUTPUT_DIR / "master_concat_list.txt"
    with open(master_concat, "w", encoding="utf-8") as f:
        for s in ordered_shots:
            f.write(f"file '{s.resolve()}'\n")

    temp_video = OUTPUT_DIR / "temp_master_video_all_36.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(master_concat),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
        "-an",
        str(temp_video)
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(AUDIO_FILE),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        str(FINAL_MV)
    ], check=True)

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(FINAL_MV), BRAIN_DIR / FINAL_MV.name)

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(FINAL_MV)],
        capture_output=True, text=True, check=True
    )
    meta = json.loads(probe.stdout)
    logger.info("============================================================")
    logger.info("🎉 ИТОГОВЫЙ КЛИП УСПЕШНО ПЕРЕСОБРАН С НОВЫМ ШОТОМ 01!")
    logger.info(f"Файл: {FINAL_MV}")
    logger.info(f"Длительность: {meta['format'].get('duration')} сек")
    logger.info(f"Размер: {int(meta['format'].get('size')) / 1024 / 1024:.2f} МБ")
    logger.info("============================================================")

if __name__ == '__main__':
    main()
