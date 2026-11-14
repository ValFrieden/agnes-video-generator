"""scripts/generate_shot_27_reflection.py
Генерация Шота 27 под слова песни:
«И строим тюрьму из пустых отражений...»
Герой смотрит в зеркало/отражающее стекло, касаясь кончиками пальцев своего отражения.
Канонический костюм (песочный кардиган + клетчатая рубашка + темные брюки).
Замок молчания (губы сжаты).
"""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Shot27Reflection")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
TARGET_MP4 = Path("output/shot_27_mirror_reflections.mp4")
CHAR_REF = Path("references/character_valeri_costume_master.png").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")

PROMPT = (
    "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
    "The same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
    "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan with ribbed cuffs over a dark grey plaid flannel button-down collared shirt, and dark charcoal straight trousers. "
    "He stands inside the dim studio room facing a tall vertical mirror. He looks closely into his own reflection with an introspective, penetrating gaze. "
    "He slowly raises his right hand and gently rests his fingertips against the cold, smooth reflective glass surface, directly touching his own mirrored reflection. "
    "In the reflective depth, subtle receding reflections of the room appear behind him. "
    "Lips strictly pressed shut, completely silent, mouth closed, no talking, no lip movement, observing in silence. "
    "Natural soft morning side-light, moody cinematic shadows, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open, no lip-sync, no jacket, no blazer"
)


async def main():
    logger.info("🚀 Запуск генерации Шота 27 («И строим тюрьму из пустых отражений»)...")
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    # 1. Возврат на холст проекта
    if "/edit/" in page.url or page.url != PROJECT_URL:
        logger.info(f"Переход на главный холст проекта: {PROJECT_URL}...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

    # 2. Очистка поля промпта
    logger.info("🧹 Очистка поля промпта...")
    await engine.clear_prompt()

    # 3. Фиксация начального состояния
    initial_tiles = await engine.get_video_tiles_count()
    prev_cards = await engine.count_cost_cards()
    logger.info(f"Начальное состояние: {initial_tiles} видео-плиток, {prev_cards} карточек стоимости.")

    # 4. Прикрепление мастер-референса костюма и лица
    logger.info(f"📎 Прикрепление мастер-референса: {CHAR_REF.name}...")
    await engine.attach_reference_image(str(CHAR_REF))
    await asyncio.sleep(1.0)

    # 5. Ввод промпта
    logger.info("✍️ Ввод промпта...")
    await engine.set_prompt(PROMPT)
    await asyncio.sleep(1.0)

    # 6. Отправка промпта
    logger.info("🚀 Отправка в Veo 3.1...")
    await engine.submit_prompt()
    await asyncio.sleep(2.0)

    # 7. Подтверждение карточки стоимости
    logger.info("⏳ Ожидание карточки стоимости...")
    card_info = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=45)
    cost = card_info.get("cost")
    if cost is not None:
        logger.info(f"💰 Карточка обнаружена: {cost} кредитов. Подтверждение...")
        await engine.approve_cost_card()
        await asyncio.sleep(1.0)
        start_btn = await page.query_selector("[aria-label*='Generierung starten'], button:has-text('Generierung starten'), [aria-label*='Start generation']")
        if start_btn and await start_btn.is_visible():
            logger.info("Нажатие кнопки 'Generierung starten'...")
            await start_btn.click(force=True)
    else:
        logger.info(f"ℹ️ Состояние карточки: {card_info}")

    # 8. Ожидание завершения генерации
    logger.info(f"⏳ Ожидание рендера видео Google Veo 3.1 (стартовое число: {initial_tiles})...")
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

    logger.info(f"✅ Шот 27 скачан: {TARGET_MP4} ({TARGET_MP4.stat().st_size} байт)")

    # 9. Извлечение кадров 25%, 50%, 75% и создание контактного листа
    logger.info("🔍 Извлечение кадров 25%, 50%, 75%...")
    qc_25 = TARGET_MP4.parent / "shot_27_qc_25.jpg"
    qc_50 = TARGET_MP4.parent / "shot_27_qc_50.jpg"
    qc_75 = TARGET_MP4.parent / "shot_27_qc_75.jpg"

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(TARGET_MP4)],
        capture_output=True, text=True, check=True
    )
    dur = float(probe.stdout.strip())
    t25 = dur * 0.25
    t50 = dur * 0.50
    t75 = dur * 0.75

    subprocess.run(["ffmpeg", "-y", "-ss", str(t25), "-i", str(TARGET_MP4), "-vframes", "1", "-q:v", "2", str(qc_25)], check=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(t50), "-i", str(TARGET_MP4), "-vframes", "1", "-q:v", "2", str(qc_50)], check=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(t75), "-i", str(TARGET_MP4), "-vframes", "1", "-q:v", "2", str(qc_75)], check=True)

    qa_contact = TARGET_MP4.parent / "shot_27_qa_trio.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(qc_25), "-i", str(qc_50), "-i", str(qc_75),
        "-filter_complex", "hstack=inputs=3",
        str(qa_contact)
    ], check=True)

    # 10. Копирование в brain
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(TARGET_MP4), BRAIN_DIR / "shot_27_mirror_reflections.mp4")
    shutil.copy2(str(qc_25), BRAIN_DIR / "shot_27_qc_25.jpg")
    shutil.copy2(str(qc_50), BRAIN_DIR / "shot_27_qc_50.jpg")
    shutil.copy2(str(qc_75), BRAIN_DIR / "shot_27_qc_75.jpg")
    shutil.copy2(str(qa_contact), BRAIN_DIR / "shot_27_qa_trio.png")

    logger.info("✅ Все файлы Шота 27 готовы и скопированы в brain.")

if __name__ == '__main__':
    asyncio.run(main())
