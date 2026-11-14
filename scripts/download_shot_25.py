import asyncio
import logging
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DownloadShot25")

TARGET_MP4 = Path("output/shot_25_cardboard_coffee.mp4")


async def main():
    engine = GoogleFlowEngine(downloads_dir=str(TARGET_MP4.parent.resolve()))
    page = await engine.connect()

    logger.info("Проверка открытого редактора или клик по тайлу...")
    # Попробуем скачать через engine.download_latest_video
    dl_path = await engine.download_latest_video(str(TARGET_MP4))
    logger.info(f"Скачано: {dl_path}, размер: {Path(dl_path).stat().st_size} байт")

    logger.info("Генерация QA-трио...")
    qa_paths = engine.generate_qa_trio(str(TARGET_MP4))
    logger.info(f"QA Trio paths: {qa_paths}")

    # Копирование в артефакты
    brain_dir = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
    for k, p in qa_paths.items():
        if Path(p).exists():
            dest = brain_dir / f"shot_25_{k}.png"
            import shutil
            shutil.copy2(p, dest)
            logger.info(f"Скопировано в артефакты: {dest}")

    print("DOWNLOAD_AND_QA_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
