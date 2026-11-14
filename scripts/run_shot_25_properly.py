"""scripts/run_shot_25_properly.py — Полный чистый цикл генерации и скачивания Шота 25 в Google Flow."""

import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Shot25Proper")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
TARGET_MP4 = Path("output/shot_25_cardboard_coffee.mp4")
CHAR_REF = Path("references/character_valeri_live_action.jpg").resolve()
STYLE_REF = Path("references/kling_style_anchors/anchor_01_wet_dock_macro.png").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")

PROMPT = (
    "Cinematic 35mm live-action film still, Kodak Vision3 500T, authentic human actor. "
    "A 42-year-old Caucasian man with short neat dark brown hair and subtle stubble beard "
    "sitting at a rustic wooden table in a paper-walled room, wearing a vintage slate tweed jacket "
    "over a dark linen shirt, no eyeglasses, lips closed. He picks up a flat 2D cardboard cutout "
    "coffee cup, looks at it with sarcastic bemusement, taps his finger against the flat paper surface "
    "showing it is fake props, real tactile textures, warm morning sunlight, master cinematography, "
    "16:9, no cartoon, no animation, no 2D, no CGI"
)


async def main():
    logger.info("🎬 Запуск честной генерации Шота 25 (Живое кино: Картонный кофе)...")
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    # 1. Возврат на холст проекта
    logger.info(f"Навигация на холст проекта: {PROJECT_URL}...")
    await page.goto(PROJECT_URL, wait_until="domcontentloaded")
    await asyncio.sleep(4.0)

    # 2. Очистить поле ввода
    logger.info("🧹 Очистка поля промпта...")
    await engine.clear_prompt()

    # 3. Фиксация начального числа плиток и карточек
    initial_tiles = await engine.get_video_tiles_count()
    prev_cards = await engine.count_cost_cards()
    logger.info(f"Начальное состояние: {initial_tiles} видео-плиток, {prev_cards} карточек стоимости.")

    # 4. Прикрепление фото живого актёра
    logger.info(f"📎 Прикрепление фото живого актёра: {CHAR_REF.name}...")
    await engine.attach_reference_image(str(CHAR_REF))

    # 5. Прикрепление якоря стиля дерева/света
    logger.info(f"📎 Прикрепление якоря стиля: {STYLE_REF.name}...")
    await engine.attach_reference_image(str(STYLE_REF))

    # 6. Ввод промпта
    logger.info(f"✍️ Ввод промпта...")
    await engine.set_prompt(PROMPT)
    await asyncio.sleep(1.0)

    # Скриншот перед отправкой
    await page.screenshot(path="output/shot_25_before_submit.png")
    logger.info("Скриншот перед отправкой сохранён.")

    # 7. Отправка промпта
    logger.info("🚀 Отправка промпта...")
    await engine.submit_prompt()
    await asyncio.sleep(2.0)

    # 8. Ожидание карточки стоимости и подтверждение
    logger.info("⏳ Ожидание карточки стоимости...")
    card_info = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=45)
    cost = card_info.get("cost")
    if cost is not None:
        logger.info(f"💰 Карточка обнаружена: {cost} кредитов. Подтверждаем...")
        approved = await engine.approve_cost_card()
        logger.info(f"Результат нажатия Approve: {approved}")
    else:
        logger.info(f"ℹ️ Карточка не появилась или генерация пошла напрямую: {card_info}")

    # Скриншот после подтверждения
    await page.screenshot(path="output/shot_25_after_approve.png")

    # 9. Ожидание завершения видео
    logger.info(f"⏳ Ожидание рендера видео Google Veo 3.1 (стартовое число плиток: {initial_tiles})...")
    completed = await engine.wait_for_video_completion(
        initial_tiles_count=initial_tiles,
        timeout_seconds=900,
        poll_interval=10.0
    )
    if not completed:
        raise TimeoutError("Время ожидания генерации видео в Google Flow истекло.")

    logger.info("🎉 Рендер завершён! Ожидание открытия редактора/скачивания...")
    await asyncio.sleep(4.0)

    # 10. Удалим старый файл перед скачиванием
    if TARGET_MP4.exists():
        TARGET_MP4.unlink()

    # 11. Скачивание нового видео
    logger.info(f"📥 Скачивание видео в {TARGET_MP4}...")
    dl_path = await engine.download_latest_video(str(TARGET_MP4))
    if not TARGET_MP4.exists():
        raise RuntimeError(f"Файл {TARGET_MP4} не появился на диске после скачивания!")

    new_size = TARGET_MP4.stat().st_size
    logger.info(f"✅ Новый Шот 25 успешно скачан: {TARGET_MP4} (размер: {new_size} байт)")

    # 12. Генерация QA-трио
    logger.info("🔍 Генерация QA-трио (25%, 50%, 75%)...")
    qa_contact = engine.generate_qa_trio(str(TARGET_MP4))
    logger.info(f"Контактный лист: {qa_contact}")

    # Копирование в brain
    shutil.copy2(str(TARGET_MP4), BRAIN_DIR / "shot_25_cardboard_coffee.mp4")
    if Path(qa_contact).exists():
        shutil.copy2(qa_contact, BRAIN_DIR / "shot_25_cardboard_coffee_qa_trio.png")

    # Извлечение отдельных кадров ffmpeg
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-ss", "1.98", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_25_action_qc_25.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "3.96", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_25_action_qc_50.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "5.95", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_25_action_qc_75.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    logger.info("🏁 ВСЕ ОПЕРАЦИИ УСПЕШНО ЗАВЕРШЕНЫ!")
    print("PROPER_GENERATION_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
