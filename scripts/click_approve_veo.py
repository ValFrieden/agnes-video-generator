"""scripts/click_approve_veo.py — Нажатие кнопки 'Genehmigen' на карточке стоимости Veo 3.1."""

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
logger = logging.getLogger("ClickApprove")


async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()

    logger.info("Поиск кнопки 'Genehmigen'...")
    # Ищем кнопку 'Genehmigen'
    btn = page.locator('button:has-text("Genehmigen")').last
    count = await btn.count()
    logger.info(f"Найдено кнопок Genehmigen: {count}")

    if count > 0:
        logger.info("Клик по кнопке Genehmigen...")
        await btn.click(force=True)
        await asyncio.sleep(2.0)
        logger.info("Успешно нажата кнопка Genehmigen!")

    await page.screenshot(path="output/after_genehmigen_click.png")
    logger.info("Скриншот после клика: output/after_genehmigen_click.png")

    body = await page.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    print("STATUS AFTER CLICK:")
    for l in lines[-15:]:
        print(" ", l)


if __name__ == "__main__":
    asyncio.run(main())
