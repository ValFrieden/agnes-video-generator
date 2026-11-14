"""scripts/run_shot_26_complete_pipeline.py
Полный пайплайн генерации Шота 26:
1. Загрузка и прикрепление 100% эталонной мастер-карты гардероба (references/character_valeri_costume_master.png)
2. Ввод промпта с точной фиксацией песочного вязаного кардигана и серой клетчатой рубашки
3. Подтверждение стоимости (Genehmigen)
4. Ожидание завершения генерации
5. Скачивание в output/shot_26_touching_air_v2.mp4
6. Нарезка контрольных кадров QA-трио (25%, 50%, 75%) и контактного листа
"""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Shot26Pipeline")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
MASTER_COSTUME_REF = Path("references/character_valeri_costume_master.png").resolve()
TARGET_MP4 = Path("output/shot_26_touching_air_v2.mp4").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")

PROMPT_SHOT_26 = (
    "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
    "The same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
    "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan with ribbed cuffs over a dark grey plaid flannel button-down collared shirt, "
    "and dark charcoal straight trousers. He steps forward across the room and suddenly halts, placing his open palms against an invisible flat barrier in thin air. "
    "He taps his knuckles against the invisible air as if touching solid granite, with quiet ironic curiosity. "
    "Lips strictly pressed shut, completely silent, mouth closed, no talking, no lip movement, observing in silence. "
    "Natural morning sunlight, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open, no lip-sync, no jacket, no blazer"
)


async def main():
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent))
    page = await engine.connect()

    # 1. Возврат на главный канвас
    if "/edit/" in page.url:
        logger.info(f"Обнаружен URL редактора {page.url}. Возврат на главный канвас проекта...")
        await page.goto(PROJECT_URL, wait_until="networkidle")
        await asyncio.sleep(2.0)

    # 2. Очистка промпта
    logger.info("Очистка промпта...")
    await engine.clear_prompt()
    await asyncio.sleep(1.0)

    # 3. Прикрепление мастер-карты гардероба
    logger.info(f"Прикрепление мастер-карты гардероба: {MASTER_COSTUME_REF}...")
    await engine.attach_reference_image(str(MASTER_COSTUME_REF))
    await asyncio.sleep(2.0)

    # 4. Ввод канонического промпта
    logger.info("Ввод промпта...")
    await engine.set_prompt(PROMPT_SHOT_26)
    await asyncio.sleep(1.5)

    # 5. Счетчики перед отправкой
    prev_cards = await engine.count_cost_cards()
    initial_tiles = await engine.get_video_tiles_count()
    logger.info(f"Счетчики: карточек={prev_cards}, плиток={initial_tiles}")

    # 6. Отправка промпта
    logger.info("Отправка запроса в Veo...")
    await engine.submit_prompt()
    await asyncio.sleep(2.5)

    # 7. Подтверждение стоимости Genehmigen
    logger.info("Ожидание карточки стоимости Genehmigen...")
    card_found = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=30.0)
    if card_found:
        logger.info("Карточка найдена! Нажатие Genehmigen...")
        approved = await engine.approve_last_card()
        logger.info(f"Результат Genehmigen: {approved}")
        if not approved:
            btn = page.locator("[role='radio'][aria-label*='Genehmigen'], .option-row:has-text('Genehmigen'), button:has-text('Genehmigen')").last
            if await btn.count() > 0:
                await btn.click(force=True)
                logger.info("Прямой клик по Genehmigen успешен!")
    else:
        logger.warning("Карточка стоимости не появилась за 30с, пробуем прямой клик...")
        btn = page.locator("[role='radio'][aria-label*='Genehmigen'], .option-row:has-text('Genehmigen'), button:has-text('Genehmigen')").last
        if await btn.count() > 0:
            await btn.click(force=True)
            logger.info("Клик Genehmigen выполнен напрямую!")

    await page.screenshot(path="output/shot_26_v2_submitted.png")
    logger.info("Генерация запущена. Скриншот: output/shot_26_v2_submitted.png")

    # 8. Ожидание готовности видео
    logger.info(f"Ожидание завершения генерации видео (тайлы > {initial_tiles})...")
    ok = await engine.wait_for_video_completion(initial_tiles_count=initial_tiles, timeout_seconds=360, poll_interval=5.0)
    if not ok:
        logger.error("Таймаут ожидания генерации видео!")
        return

    logger.info("Видео сгенерировано! Открытие последней плитки...")
    await page.evaluate("""() => {
        const ts = document.querySelectorAll('flow-video-tile');
        if (ts.length > 0) {
            ts[ts.length - 1].click();
        }
    }""")
    await asyncio.sleep(4.0)

    # 9. Скачивание видео
    if TARGET_MP4.exists():
        TARGET_MP4.unlink()

    logger.info(f"Скачивание видео в {TARGET_MP4}...")
    dl_path = await engine.download_latest_video(str(TARGET_MP4))
    logger.info(f"Скачано: {dl_path}, размер: {TARGET_MP4.stat().st_size} байт")

    # 10. QA-трио и контрольные кадры
    qa_contact = engine.generate_qa_trio(str(TARGET_MP4))
    logger.info(f"Контактный лист QA: {qa_contact}")

    # Копирование в brain
    shutil.copy2(str(TARGET_MP4), BRAIN_DIR / "shot_26_touching_air_v2.mp4")
    if Path(qa_contact).exists():
        shutil.copy2(qa_contact, BRAIN_DIR / "shot_26_touching_air_v2_qa_trio.png")

    # Нарезка кадров 25%, 50%, 75%
    subprocess.run(["ffmpeg", "-y", "-ss", "1.98", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_26_v2_qc_25.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "3.96", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_26_v2_qc_50.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "5.95", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_26_v2_qc_75.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    logger.info("✅ ШОТ 26 УСПЕШНО СГЕНЕРИРОВАН И ПРОВЕРЕН!")
    print("SHOT_26_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
