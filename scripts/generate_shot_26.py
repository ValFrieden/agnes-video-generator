"""scripts/generate_shot_26.py — Генерация Шота 26: «Мы трогаем воздух, считая гранитом...»."""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Shot26")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
TARGET_MP4 = Path("output/shot_26_touching_air.mp4")
CHAR_REF = Path("references/character_valeri_live_action.jpg").resolve()
STYLE_REF = Path("references/kling_style_anchors/anchor_01_wet_dock_macro.png").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")

PROMPT = (
    "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
    "The same 42-year-old Caucasian man with short neat dark brown hair and subtle stubble beard wearing a vintage "
    "slate tweed jacket over a dark linen shirt, identical appearance to reference image, no eyeglasses. "
    "He steps forward across the room and suddenly halts as both of his open palms meet an invisible flat barrier in thin air. "
    "He taps his knuckles against the invisible air as if touching solid granite, feeling the invisible wall with curious ironic amusement. "
    "His lips are strictly pressed shut, completely silent, mouth closed, no talking, no lip movement, observing in silence. "
    "Natural morning light, authentic film grain, master cinematography, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open, no lip-sync"
)


async def main():
    logger.info("🚀 Запуск генерации Шота 26 («Мы трогаем воздух, считая гранитом...»)...")
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    # 1. Защита от зависания в /edit/: принудительный переход на холст проекта
    if "/edit/" in page.url or page.url != PROJECT_URL:
        logger.info(f"Переход на холст проекта: {PROJECT_URL}...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

    # 2. Очистка поля промпта
    logger.info("🧹 Очистка поля ввода...")
    await engine.clear_prompt()

    # 3. Фиксация начального состояния
    initial_tiles = await engine.get_video_tiles_count()
    prev_cards = await engine.count_cost_cards()
    logger.info(f"Начальное состояние: {initial_tiles} видео-плиток, {prev_cards} карточек стоимости.")

    # 4. Прикрепление фото живого актёра (строгая консистентность лица)
    logger.info(f"📎 Прикрепление фото актёра: {CHAR_REF.name}...")
    await engine.attach_reference_image(str(CHAR_REF))

    # 5. Прикрепление якоря стиля света
    logger.info(f"📎 Прикрепление якоря стиля: {STYLE_REF.name}...")
    await engine.attach_reference_image(str(STYLE_REF))

    # 6. Ввод промпта
    logger.info("✍️ Ввод промпта...")
    await engine.set_prompt(PROMPT)
    await asyncio.sleep(1.0)

    # 7. Отправка в Veo 3.1
    logger.info("🚀 Отправка в Veo 3.1...")
    await engine.submit_prompt()
    await asyncio.sleep(2.0)

    # 8. Автоматическое подтверждение карточки стоимости
    logger.info("⏳ Ожидание карточки стоимости...")
    card_info = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=45)
    cost = card_info.get("cost")
    if cost is not None:
        logger.info(f"💰 Карточка обнаружена: {cost} кредитов. Нажатие Genehmigen...")
        approved = await engine.approve_cost_card()
        logger.info(f"Результат нажатия Genehmigen: {approved}")
    else:
        logger.info(f"ℹ️ Генерация началась: {card_info}")

    # 9. Ожидание завершения генерации
    logger.info(f"⏳ Ожидание рендера видео Veo 3.1 (стартовое число: {initial_tiles})...")
    completed = await engine.wait_for_video_completion(
        initial_tiles_count=initial_tiles,
        timeout_seconds=900,
        poll_interval=10.0
    )
    if not completed:
        raise TimeoutError("Время ожидания генерации видео в Google Flow истекло.")

    logger.info("🎉 Рендер завершен! Скачивание видео...")
    await asyncio.sleep(3.0)

    if TARGET_MP4.exists():
        TARGET_MP4.unlink()

    dl_path = await engine.download_latest_video(str(TARGET_MP4))
    if not TARGET_MP4.exists():
        raise RuntimeError(f"Файл {TARGET_MP4} не был скачан!")

    logger.info(f"✅ Шот 26 скачан: {TARGET_MP4} ({TARGET_MP4.stat().st_size} байт)")

    # 10. Генерация QA-трио
    logger.info("🔍 Генерация QA-трио...")
    qa_contact = engine.generate_qa_trio(str(TARGET_MP4))

    # Копирование в brain
    shutil.copy2(str(TARGET_MP4), BRAIN_DIR / "shot_26_touching_air.mp4")
    if Path(qa_contact).exists():
        shutil.copy2(qa_contact, BRAIN_DIR / "shot_26_touching_air_qa_trio.png")

    subprocess.run(["ffmpeg", "-y", "-ss", "1.98", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_26_qc_25.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "3.96", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_26_qc_50.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "5.95", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_26_qc_75.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    logger.info("🏁 ВСЕ ОПЕРАЦИИ ВЫПОЛНЕНЫ УСПЕШНО!")
    print("SHOT_26_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
