"""scripts/generate_shot_28_peeling_scenery.py
Генерация Шота 28 под слова песни:
«А может быть, это искусный обман...»
Сюжет: Бутафорские бумажные декорации стены начинают отклеиваться и расходиться по вертикальному шву;
сквозь образовавшийся зазор в полумрак комнаты пробиваются яркие золотистые лучи утреннего солнца (god rays).
Герой смотрит на этот свет с осознанием и надеждой.
Канонический костюм: песочный кардиган + темно-серая клетчатая фланелевая рубашка + темные брюки.
Замок молчания: губы плотно сжаты, рот закрыт.
Физическая достоверность: бумага отслаивается естественно, падая вниз под силой тяжести, без магии и фантастики.
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
logger = logging.getLogger("Shot28Scenery")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
TARGET_MP4 = Path("output/shot_28_peeling_scenery.mp4")
CHAR_REF = Path("references/character_valeri_costume_master.png").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")

PROMPT = (
    "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
    "The same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
    "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan with ribbed cuffs over a dark grey plaid flannel button-down collared shirt, and dark charcoal straight trousers. "
    "He stands inside the dim room observing the fake stage wall in front of him. A vertical seam of the heavy craft paper wallpaper naturally loosens and peels open downwards under gravity. "
    "Through the widening vertical gap in the paper wall, brilliant warm golden morning sunlight pierces into the dim room, casting intense cinematic volumetric light beams (god rays) and illuminating floating dust particles. "
    "The man observes the golden light breaking through with calm, profound realization and quiet wonder. "
    "Lips strictly pressed shut, completely silent, mouth closed, no talking, no lip movement, observing in silence. "
    "Realistic physical gravity, moody contrast between cold shadow and golden dawn sunlight, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open, no upward flying paper, no sci-fi shutters"
)


async def dismiss_any_modal(page):
    """Закрывает любые всплывающие окна (например, чейнджлог 'Alle Änderungsprotokolle / Jetzt starten')."""
    try:
        has_dialog = await page.evaluate("() => document.querySelectorAll('.cdk-overlay-backdrop-showing, mat-dialog-container').length > 0")
        if has_dialog:
            logger.info("⚠️ Обнаружен модальный диалог, закрываем...")
            await page.keyboard.press("Escape")
            await asyncio.sleep(1.0)
            btn = await page.query_selector("mat-dialog-container button, .cdk-overlay-pane button")
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(1.0)
    except Exception as e:
        logger.warning(f"Ошибка при закрытии диалога: {e}")


async def download_shot(page, target_path: Path):
    """Надежное скачивание 720p через DOM поиск в Playwright"""
    logger.info("Скачивание 720p видео...")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()

    # Проверяем кнопку Download
    btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
    if btn and await btn.is_visible():
        logger.info("Кнопка 'Download' видна в редакторе.")
    else:
        logger.info("Открытие первой видео-плитки...")
        opened = await page.evaluate("""(() => {
            const tiles = document.querySelectorAll('flow-video-tile');
            if (tiles.length > 0) {
                tiles[0].click();
                return true;
            }
            return false;
        })()""")
        await asyncio.sleep(2.0)

    async with page.expect_download(timeout=60000) as dl_info:
        # Открываем меню скачивания если еще не открыто
        btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
        if btn:
            await btn.click()
            await asyncio.sleep(1.0)

        # Кликаем 720p
        clicked = await page.evaluate("""(() => {
            const all = Array.from(document.querySelectorAll('*'));
            const opt = all.find(el => el.innerText && el.innerText.includes('720p') && (
                el.getAttribute('role') === 'menuitem' || 
                el.tagName === 'BUTTON' || 
                el.classList.contains('mat-mdc-menu-item') ||
                el.tagName === 'SPAN'
            ));
            if (opt) {
                const clickTarget = opt.closest('button') || opt.closest('[role=\"menuitem\"]') || opt;
                clickTarget.click();
                return true;
            }
            return false;
        })()""")
        logger.info(f"Клик по элементу 720p: {clicked}")
        if not clicked:
            raise RuntimeError("Не удалось найти и кликнуть пункт меню 720p!")

    download = await dl_info.value
    await download.save_as(str(target_path))
    logger.info(f"✅ Файл успешно сохранен: {target_path} ({target_path.stat().st_size} байт)")


async def main():
    logger.info("🚀 Запуск генерации Шота 28 («А может быть, это искусный обман...»)...")
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    # 1. Возврат на холст проекта
    if "/edit/" in page.url or page.url != PROJECT_URL:
        logger.info(f"Переход на главный холст проекта: {PROJECT_URL}...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

    # Закрываем любые всплывающие окна
    await dismiss_any_modal(page)

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
    logger.info(f"⏳ Ожидание рендера видео Google Veo 3.1 (стартовое число плиток: {initial_tiles})...")
    completed = await engine.wait_for_video_completion(
        initial_tiles_count=initial_tiles,
        timeout_seconds=900,
        poll_interval=10.0
    )
    if not completed:
        raise TimeoutError("Время ожидания генерации видео в Google Flow истекло.")

    logger.info("🎉 Рендер завершен! Скачивание видео...")
    await asyncio.sleep(3.0)

    # 9. Надежное скачивание
    await download_shot(page, TARGET_MP4)

    if not TARGET_MP4.exists() or TARGET_MP4.stat().st_size < 300000:
        raise RuntimeError(f"Файл {TARGET_MP4} поврежден или отсутствует!")

    # 10. Извлечение кадров 25%, 50%, 75% и создание контактного листа
    logger.info("🔍 Извлечение кадров 25%, 50%, 75%...")
    qc_25 = TARGET_MP4.parent / "shot_28_qc_25.jpg"
    qc_50 = TARGET_MP4.parent / "shot_28_qc_50.jpg"
    qc_75 = TARGET_MP4.parent / "shot_28_qc_75.jpg"

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

    qa_contact = TARGET_MP4.parent / "shot_28_qa_trio.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(qc_25), "-i", str(qc_50), "-i", str(qc_75),
        "-filter_complex", "hstack=inputs=3",
        str(qa_contact)
    ], check=True)

    # 11. Копирование в brain
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(TARGET_MP4), BRAIN_DIR / "shot_28_peeling_scenery.mp4")
    shutil.copy2(str(qc_25), BRAIN_DIR / "shot_28_qc_25.jpg")
    shutil.copy2(str(qc_50), BRAIN_DIR / "shot_28_qc_50.jpg")
    shutil.copy2(str(qc_75), BRAIN_DIR / "shot_28_qc_75.jpg")
    shutil.copy2(str(qa_contact), BRAIN_DIR / "shot_28_qa_trio.png")

    logger.info("✅ Все файлы Шота 28 готовы и скопированы в brain.")

if __name__ == '__main__':
    asyncio.run(main())
