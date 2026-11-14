"""scripts/generate_action_shot_25.py — Генерация Шота 25: Живое кино (35mm Live-Action) «Картонный кофе»."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Shot25LiveAction")

TARGET_MP4 = Path("output/shot_25_cardboard_coffee.mp4")
CHAR_REF = Path("references/character_valeri_live_action.jpg").resolve()
STYLE_REF = Path("references/kling_style_anchors/anchor_01_wet_dock_macro.png").resolve()

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
    logger.info("🎬 Запуск генерации Шота 25 (Живое кино: Картонный кофе)...")
    logger.info(f"  • Персонаж-референс (Живой актёр): {CHAR_REF}")
    logger.info(f"  • Якорь стиля дерева/света: {STYLE_REF}")
    logger.info(f"  • Выходной файл: {TARGET_MP4}")

    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    # 1. Возврат на холст, если открыт редактор
    await engine.exit_editor_if_open()

    # 2. Очистить поле промпта от старых чипов
    logger.info("🧹 Очистка поля промпта...")
    await engine.clear_prompt()

    # 3. Прикрепить референс живого актёра
    logger.info(f"📎 Прикрепление фото живого актёра: {CHAR_REF.name}...")
    await engine.attach_reference_image(str(CHAR_REF))

    # 4. Прикрепить якорь стиля мокрого дерева/света
    logger.info(f"📎 Прикрепление якоря стиля: {STYLE_REF.name}...")
    await engine.attach_reference_image(str(STYLE_REF))

    # 5. Подсчитать исходное количество карточек затрат
    prev_cards = await engine.count_cost_cards()

    # 6. Ввести промпт и отправить
    logger.info(f"✍️ Ввод промпта: {PROMPT[:80]}...")
    await engine.set_prompt(PROMPT)
    await engine.submit_prompt()

    # 7. Подтвердить стоимость (10 кредитов)
    logger.info("⏳ Ожидание карточки подтверждения стоимости...")
    card_info = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=45)
    cost = card_info.get("cost")
    if cost is not None:
        logger.info(f"💰 Карточка обнаружена: {cost} кредитов. Подтверждаем...")
        await engine.approve_cost_card()
    else:
        logger.info(f"ℹ️ Генерация продолжилась: {card_info}")

    # 8. Ожидание завершения генерации
    logger.info("⏳ Ожидание завершения рендера видео Google Veo 3.1...")
    completed = await engine.wait_for_video_completion(poll_interval=15, timeout_seconds=900)
    if not completed:
        raise TimeoutError("Время ожидания генерации видео в Google Flow истекло (15 мин).")

    # 9. Скачивание готового MP4
    logger.info(f"📥 Скачивание видео в {TARGET_MP4}...")
    downloaded = await engine.download_latest_video(str(TARGET_MP4))
    if not downloaded or not TARGET_MP4.exists():
        raise RuntimeError(f"Не удалось скачать шот в {TARGET_MP4}")

    logger.info(f"✅ Шот 25 успешно сохранён: {TARGET_MP4} ({TARGET_MP4.stat().st_size} байт)")

    # 10. Создание QA-трио (25%, 50%, 75% + контактный лист)
    logger.info("🔍 Извлечение контрольных кадров QA-трио...")
    qa_paths = engine.generate_qa_trio(str(TARGET_MP4))
    logger.info(f"📸 Контрольные кадры сохранены: {qa_paths}")

    print("ALL_DONE_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
