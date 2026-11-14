"""scripts/assemble_all_36_direct.py
Прямая безошибочная склейка всех 36 индивидуальных шотов (01-36)
с новым Шотом 01 и оригинальным мастер-аудиотреком (219 сек).
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
logger = logging.getLogger("Assemble36Direct")

OUTPUT_DIR = Path("output").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
AUDIO_FILE = Path("uploaded_media_1793789661300.mp3").resolve()
FINAL_MV = OUTPUT_DIR / "metamorfoza_materii_final_full_mv.mp4"

ALL_36_SHOTS = [
    OUTPUT_DIR / "shot_01_single_panel.mp4",
    OUTPUT_DIR / "shot_02_room_cube.mp4",
    OUTPUT_DIR / "shot_03_sealed_cube.mp4",
    OUTPUT_DIR / "shot_04_light_burst.mp4",
    OUTPUT_DIR / "shot_05_dense_mist.mp4",
    OUTPUT_DIR / "shot_06_condensation_drips.mp4",
    OUTPUT_DIR / "shot_07_paper_sags.mp4",
    OUTPUT_DIR / "shot_08_water_reflection.mp4",
    OUTPUT_DIR / "shot_09_cracking_cube.mp4",
    OUTPUT_DIR / "shot_10_smoldering_embers.mp4",
    OUTPUT_DIR / "shot_11_walls_to_ash.mp4",
    OUTPUT_DIR / "shot_12_emerald_sprout.mp4",
    OUTPUT_DIR / "shot_13_blossomed_flower.mp4",
    OUTPUT_DIR / "shot_14_airborne_dew.mp4",
    OUTPUT_DIR / "shot_15_wide_lake.mp4",
    OUTPUT_DIR / "shot_16_open_horizon.mp4",
    OUTPUT_DIR / "shot_17_dew_prisms.mp4",
    OUTPUT_DIR / "shot_18_mirror_ripples.mp4",
    OUTPUT_DIR / "shot_19_swaying_flower.mp4",
    OUTPUT_DIR / "shot_20_glide_horizon.mp4",
    OUTPUT_DIR / "shot_21_ember_vortex.mp4",
    OUTPUT_DIR / "shot_22_tear_veil.mp4",
    OUTPUT_DIR / "shot_23_blazing_sunrise.mp4",
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
    logger.info("🎬 ПРЯМАЯ СКЛЕЙКА ВСЕХ 36 ШОТОВ (01-36)...")

    missing = [str(f.name) for f in ALL_36_SHOTS if not f.exists()]
    if missing:
        logger.error(f"❌ Отсутствуют файлы: {missing}")
        sys.exit(1)

    concat_file = OUTPUT_DIR / "all_36_direct_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for s in ALL_36_SHOTS:
            f.write(f"file '{s.resolve()}'\n")

    temp_video = OUTPUT_DIR / "temp_full_36_visuals_direct.mp4"

    logger.info("1. Склейка 36 шотов в единый видеоряд 1280x720 24fps...")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
        "-an",
        str(temp_video)
    ], check=True)

    logger.info("2. Наложение оригинального мастер-аудио...")
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
    logger.info("🎉 ИТОГОВЫЙ ПОЛНЫЙ ФИЛЬМ УСПЕШНО СОБРАН ИЗ 36 ШОТОВ!")
    logger.info(f"Файл: {FINAL_MV}")
    logger.info(f"Длительность: {meta['format'].get('duration')} сек (03:39)")
    logger.info(f"Размер: {int(meta['format'].get('size')) / 1024 / 1024:.2f} МБ")
    logger.info("============================================================")

if __name__ == '__main__':
    main()
