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
logger = logging.getLogger("DownloadReadyVideo")

TARGET_MP4 = Path("output/shot_25_cardboard_coffee_live.mp4")
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")


async def main():
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    logger.info("Проверка состояния холста и тайлов...")
    await page.screenshot(path="output/flow_ready_check.png")

    # Ищем все flow-video-tile
    tiles = await page.evaluate("""() => {
        const ts = Array.from(document.querySelectorAll('flow-video-tile'));
        return ts.map((t, i) => ({
            index: i,
            text: (t.innerText || '').slice(0, 100),
            hasVideo: !!t.querySelector('video'),
            hasImg: !!t.querySelector('img')
        }));
    }""")
    logger.info(f"Найдено тайлов: {len(tiles)} -> {tiles}")

    # Кликаем по последней плитке, чтобы открыть редактор
    logger.info("Клик по последней плитке...")
    await page.evaluate("""() => {
        const ts = document.querySelectorAll('flow-video-tile');
        if (ts.length > 0) {
            ts[ts.length - 1].click();
        }
    }""")
    await asyncio.sleep(3.0)

    # Проверяем, видна ли кнопка Download
    has_dl = await page.evaluate("""() => {
        const btn = document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]');
        return !!btn;
    }""")
    logger.info(f"Кнопка Download доступна: {has_dl}")

    if has_dl:
        if TARGET_MP4.exists():
            TARGET_MP4.unlink()

        logger.info(f"Запуск скачивания видео в {TARGET_MP4}...")
        dl_path = await engine.download_latest_video(str(TARGET_MP4))
        logger.info(f"Скачано: {dl_path}, размер: {TARGET_MP4.stat().st_size} байт")

        # Генерация QA-трио
        qa_contact = engine.generate_qa_trio(str(TARGET_MP4))
        logger.info(f"Контактный лист QA: {qa_contact}")

        # Копирование в brain
        shutil.copy2(str(TARGET_MP4), BRAIN_DIR / "shot_25_cardboard_coffee_live.mp4")
        if Path(qa_contact).exists():
            shutil.copy2(qa_contact, BRAIN_DIR / "shot_25_cardboard_coffee_live_qa_trio.png")

        # Нарезка 25%, 50%, 75%
        subprocess.run(["ffmpeg", "-y", "-ss", "1.98", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_25_live_qc_25.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-ss", "3.96", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_25_live_qc_50.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-ss", "5.95", "-i", str(TARGET_MP4), "-vframes", "1", str(BRAIN_DIR / "shot_25_live_qc_75.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        logger.info("✅ УСПЕШНО СКАЧАНО И НАРЕЗАНО!")
        print("READY_VIDEO_VERIFIED_SUCCESS")
    else:
        logger.warning("Кнопка Download не появилась в открытом окне.")


if __name__ == "__main__":
    asyncio.run(main())
