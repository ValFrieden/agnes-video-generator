"""scripts/generate_shot_26_gravity_fix.py
Перегенерация Шота 26 с железной физикой гравитации:
- Герой стучит по бутафорской «гранитной» стене.
- При ударе хрупкая поверхность проламывается: куски штукатурки, обрывки крафтовой бумаги и крошка
  осыпаются СТРОГО ВНИЗ на дощатый пол под действием реальной земной гравитации.
- Никакого движения наверх, никаких раздвижных створок или оригами.
- Канонический костюм: песочный кардиган + фланелевая рубашка в клетку + темные брюки.
- Полное молчание, губы сжаты.
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
logger = logging.getLogger("Shot26GravityFix")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
TARGET_MP4 = Path("output/shot_26_gravity_crumble.mp4")
CHAR_REF = Path("references/character_valeri_costume_master.png").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")

PROMPT = (
    "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
    "The same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
    "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan with ribbed cuffs over a dark grey plaid flannel button-down collared shirt, and dark charcoal straight trousers. "
    "He steps firmly up to a painted studio wall that imitates rough grey granite stone. He raises his right fist and knocks firmly against the wall expecting solid stone. "
    "Under the impact of his knuckles, the fragile wall fractures and breaks: brittle plaster flakes, torn shreds of craft paper, and broken cardboard chunks crumble and drop straight down onto the wooden floorboards under natural downward gravity. "
    "A jagged, torn puncture hole breaks open in the wall, with small dust crumbs tumbling downward to the ground, revealing the dark hollow cavity behind the fake stage scenery. "
    "The man lowers his hand and quietly looks down at the fallen debris on the floor with calm, knowing irony. "
    "Strict downward gravity physics, debris falls down onto floorboards, no upward motion, no shutters, no origami, no sliding panels, no floating debris. "
    "Lips strictly pressed shut, completely silent, mouth closed, no talking, no lip movement, observing in silence. "
    "Natural morning light, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open, no lip-sync, no jacket, no blazer, no mime"
)


async def main():
    logger.info("🚀 Запуск генерации Шота 26 (Физика гравитации: обсыпание обломков вниз)...")
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

    # 5. Ввод промпта с акцентом на гравитацию
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

    logger.info(f"✅ Шот 26 скачан: {TARGET_MP4} ({TARGET_MP4.stat().st_size} байт)")

    # 9. Извлечение кадров 25%, 50%, 75% и создание контактного листа
    logger.info("🔍 Извлечение кадров 25%, 50%, 75%...")
    qc_25 = TARGET_MP4.parent / "shot_26_g_qc_25.jpg"
    qc_50 = TARGET_MP4.parent / "shot_26_g_qc_50.jpg"
    qc_75 = TARGET_MP4.parent / "shot_26_g_qc_75.jpg"

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

    qa_contact = TARGET_MP4.parent / "shot_26_g_qa_trio.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(qc_25), "-i", str(qc_50), "-i", str(qc_75),
        "-filter_complex", "hstack=inputs=3",
        str(qa_contact)
    ], check=True)

    # 10. Копирование в brain
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(TARGET_MP4), BRAIN_DIR / "shot_26_gravity_crumble.mp4")
    shutil.copy2(str(qc_25), BRAIN_DIR / "shot_26_g_qc_25.jpg")
    shutil.copy2(str(qc_50), BRAIN_DIR / "shot_26_g_qc_50.jpg")
    shutil.copy2(str(qc_75), BRAIN_DIR / "shot_26_g_qc_75.jpg")
    shutil.copy2(str(qa_contact), BRAIN_DIR / "shot_26_g_qa_trio.png")

    logger.info("✅ Все файлы готовы и скопированы в brain.")

if __name__ == '__main__':
    asyncio.run(main())
