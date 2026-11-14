"""scripts/generate_shot_01_cube_fold.py
Генерация нового Шота 01 с точным складыванием бумажного листа
в открытый бумажный домик-куб из Шота 02 (shot_02_start_frame.jpg).
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
logger = logging.getLogger("Shot01CubeFold")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
CUBE_REF = Path("references/shot_02_target_cube.png").resolve()
OUTPUT_DIR = Path("output").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
TARGET_MP4 = OUTPUT_DIR / "shot_01_single_panel_new.mp4"

PROMPT = (
    "Generate video with Veo: Cinematic 35mm live-action motion video, natural color grading. "
    "A flat, heavy textured white watercolor paper sheet lies on a dark wet rustic wooden pier above a calm misty lake at dawn. "
    "The paper sheet naturally folds along crisp straight crease lines, with three side panels smoothly rising upright at clean 90-degree right angles to form the exact open-top square paper room cube shown in the attached reference image. "
    "As the paper walls stand upright, the interior reveals clean hand-drawn pencil perspective lines of a room and a small hand-drawn yellow watercolor sun on the back wall. "
    "Realistic paper folding physics, warm morning sunlight, calm misty lake water in soft blurred background, 16:9 widescreen, "
    "no pop-up cathedral, no arched roofs, no church, no window cutouts, no castle, no complex origami, no borders, no film frame, edge-to-edge video, no cartoon, no animation, no 2D, no CGI"
)


async def dismiss_any_modal(page):
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


async def wait_for_tile_0_ready(page, timeout_seconds=600, poll_interval=5.0):
    start_time = time.time()
    logger.info("⏳ Ожидание завершения генерации Шота 01...")
    await asyncio.sleep(12.0)
    while (time.time() - start_time) < timeout_seconds:
        status = await page.evaluate('''() => {
            const editor = !!document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]');
            const firstTile = document.querySelector('flow-video-tile');
            const hasPlayCircle = firstTile ? (firstTile.innerText || '').includes('play_circle') : false;
            const video = firstTile ? firstTile.querySelector('video') : null;
            const hasVideo = !!(video && video.src && video.src.length > 20);
            const text = (firstTile ? firstTile.innerText : '') || document.body.innerText || '';
            const match = text.match(/(\\d+)\\s*%/);
            const hasProgress = !!match;
            const hasSpinner = !!document.querySelector('mat-progress-spinner, mat-spinner, .loading, .spinner');
            return {
                ready: (hasVideo || editor || hasPlayCircle) && !hasProgress && !hasSpinner,
                editor,
                hasPlayCircle,
                progress: match ? match[1] : null,
                hasVideo,
                hasSpinner
            };
        }''')
        elapsed = int(time.time() - start_time)
        if status.get("ready"):
            logger.info(f"🎉 [+{elapsed}s] Видео отрендерено! (editor={status.get('editor')}, play_circle={status.get('hasPlayCircle')})")
            await asyncio.sleep(2.0)
            return True
        elif status.get("progress"):
            logger.info(f"⏳ [+{elapsed}s] Прогресс: {status['progress']}%")
        else:
            logger.info(f"⏳ [+{elapsed}s] Рендеринг в процессе...")
        await asyncio.sleep(poll_interval)
    raise TimeoutError(f"Превышено время ожидания рендера ({timeout_seconds}с)")


async def download_shot(page, target_path: Path):
    logger.info(f"📥 Скачивание 720p видео в {target_path.name}...")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()

    btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
    if not (btn and await btn.is_visible()):
        logger.info("Открытие первой видео-плитки...")
        await page.evaluate("""(() => {
            const tiles = document.querySelectorAll('flow-video-tile');
            if (tiles.length > 0) tiles[0].click();
        })()""")
        await asyncio.sleep(2.0)

    async with page.expect_download(timeout=60000) as dl_info:
        btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
        if btn:
            await btn.click()
            await asyncio.sleep(1.0)

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
    logger.info(f"✅ Файл сохранен: {target_path} ({target_path.stat().st_size} байт)")


def extract_qc_frames(target_path: Path):
    qc_25 = target_path.parent / f"{target_path.stem}_qc_25.jpg"
    qc_50 = target_path.parent / f"{target_path.stem}_qc_50.jpg"
    qc_75 = target_path.parent / f"{target_path.stem}_qc_75.jpg"

    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(target_path)]
    ).decode().strip())

    subprocess.run(["ffmpeg", "-y", "-ss", str(dur * 0.25), "-i", str(target_path), "-vframes", "1", "-q:v", "2", str(qc_25)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(dur * 0.50), "-i", str(target_path), "-vframes", "1", "-q:v", "2", str(qc_50)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(dur * 0.75), "-i", str(target_path), "-vframes", "1", "-q:v", "2", str(qc_75)], check=True, capture_output=True)

    qa_contact = target_path.parent / f"{target_path.stem}_qa_trio.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(qc_25), "-i", str(qc_50), "-i", str(qc_75),
        "-filter_complex", "hstack=inputs=3",
        str(qa_contact)
    ], check=True, capture_output=True)

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(target_path), BRAIN_DIR / target_path.name)
    shutil.copy2(str(qc_25), BRAIN_DIR / qc_25.name)
    shutil.copy2(str(qc_50), BRAIN_DIR / qc_50.name)
    shutil.copy2(str(qc_75), BRAIN_DIR / qc_75.name)
    shutil.copy2(str(qa_contact), BRAIN_DIR / qa_contact.name)
    logger.info(f"📸 QC-кадры скопированы в brain: {qa_contact.name}")


async def main():
    logger.info("🚀 Запуск генерации нового Шота 01 (складывание куба из Шота 02)...")
    engine = GoogleFlowEngine(downloads_dir=str(OUTPUT_DIR))
    page = await engine.connect()

    if "/edit/" in page.url or page.url != PROJECT_URL:
        logger.info(f"Переход на главный холст проекта: {PROJECT_URL}...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

    await dismiss_any_modal(page)

    logger.info("🧹 Очистка поля промпта...")
    await engine.clear_prompt()

    prev_cards = await engine.count_cost_cards()

    logger.info(f"📎 Прикрепление целевого референса куба: {CUBE_REF.name}...")
    await engine.attach_reference_image(str(CUBE_REF))
    await asyncio.sleep(1.0)

    logger.info("✍️ Ввод выверенного промпта...")
    await engine.set_prompt(PROMPT)
    await asyncio.sleep(1.0)

    logger.info("🚀 Отправка в Veo 3.1...")
    await engine.submit_prompt()
    await asyncio.sleep(2.0)

    logger.info("⏳ Ожидание карточки стоимости...")
    card_info = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=45)
    cost = card_info.get("cost")
    if cost is not None:
        logger.info(f"💰 Карточка стоимости: {cost} кредитов. Подтверждаем...")
        await engine.approve_cost_card()
        await asyncio.sleep(1.0)
        start_btn = await page.query_selector("[aria-label*='Generierung starten'], button:has-text('Generierung starten'), [aria-label*='Start generation']")
        if start_btn and await start_btn.is_visible():
            await start_btn.click(force=True)

    await wait_for_tile_0_ready(page, timeout_seconds=900)

    logger.info("🎉 Рендер завершен! Скачивание...")
    await asyncio.sleep(2.0)
    await download_shot(page, TARGET_MP4)

    if not TARGET_MP4.exists() or TARGET_MP4.stat().st_size < 300000:
        raise RuntimeError(f"Файл {TARGET_MP4} поврежден или отсутствует!")

    extract_qc_frames(TARGET_MP4)
    logger.info("✅ Новый Шот 01 успешно сгенерирован и проверен!")


if __name__ == '__main__':
    asyncio.run(main())
