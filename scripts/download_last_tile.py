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
logger = logging.getLogger("DownloadClip")

TARGET_MP4 = Path("output/shot_25_cardboard_coffee.mp4")


async def main():
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    logger.info("Открытие редактора последней сгенерированной плитки...")
    # Нажмем на последнюю плитку (tiles[2])
    opened = await page.evaluate("""() => {
        const tiles = document.querySelectorAll('flow-video-tile');
        if (tiles.length > 0) {
            // Кликаем по последней плитке
            const lastTile = tiles[tiles.length - 1];
            lastTile.click();
            return true;
        }
        return false;
    }""")
    logger.info(f"Клик по тайлу: {opened}")
    await asyncio.sleep(3.0)

    # Скриншот открытого редактора
    await page.screenshot(path="output/shot_25_editor_open.png")
    logger.info("Скриншот сохранён: output/shot_25_editor_open.png")

    # Проверим, видна ли кнопка скачивания
    has_dl = await page.evaluate("""() => {
        const btn = document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]');
        return !!btn;
    }""")
    logger.info(f"Кнопка Download обнаружена: {has_dl}")

    if has_dl:
        # Скачиваем файл через скачивание в браузере
        logger.info("Запуск загрузки через кнопку меню...")
        dl_path = await engine.download_latest_video(str(TARGET_MP4))
        logger.info(f"Файл успешно скачан в: {dl_path}")

        # Генерация QA-трио
        logger.info("Извлечение контрольных кадров QA-трио...")
        qa_paths = engine.generate_qa_trio(str(TARGET_MP4))
        logger.info(f"Контрольные кадры: {qa_paths}")

        # Копирование в артефакты
        brain_dir = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
        import shutil
        for k, p in qa_paths.items():
            if Path(p).exists():
                dest = brain_dir / f"shot_25_{k}.jpg"
                shutil.copy2(p, dest)
                logger.info(f"Скопировано в артефакты: {dest}")

        # Скопируем и само видео в артефакты
        shutil.copy2(str(TARGET_MP4), brain_dir / "shot_25_cardboard_coffee.mp4")
        print("SUCCESS_DOWNLOAD_AND_QA")
    else:
        logger.warning("Редактор не открыл кнопку Download. Возможно, рендер еще идет или тайл другой.")


if __name__ == "__main__":
    asyncio.run(main())
