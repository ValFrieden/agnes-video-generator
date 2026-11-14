"""scripts/regenerate_shot_26_with_costume.py
Повторная генерация Шота 26 с железной фиксацией канонической одежды:
- Песочно-бежевый фактурный вязаный кардиган крупной вязки с манжетами
- Серо-темная фланелевая рубашка в клетку
- Темно-графитовые прямые брюки
- Референс: references/character_valeri_costume_master.png
- Полное молчание (губы сомкнуты)
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Shot26CostumeLock")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
MASTER_COSTUME_REF = Path("references/character_valeri_costume_master.png").resolve()

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
    engine = GoogleFlowEngine()
    page = await engine.connect()

    # 1. Возвращаемся из полноэкранного редактора /edit/ в канвас проекта
    if "/edit/" in page.url:
        logger.info(f"Обнаружен URL редактора {page.url}. Возврат на главный канвас проекта...")
        await page.goto(PROJECT_URL, wait_until="networkidle")
        await asyncio.sleep(2.0)

    logger.info("Проверка состояния канваса...")
    await page.wait_for_selector("textarea, [contenteditable='true']", timeout=15000)

    # 2. Очистка поля ввода
    logger.info("Очистка промпта...")
    await engine.clear_prompt()
    await asyncio.sleep(1.0)

    # 3. Прикрепление мастер-карты гардероба и персонажа
    logger.info(f"Прикрепление мастер-карты гардероба: {MASTER_COSTUME_REF}...")
    await engine.attach_reference_image(str(MASTER_COSTUME_REF))
    await asyncio.sleep(2.0)

    # 4. Ввод канонического промпта
    logger.info("Ввод промпта с железной фиксацией одежды...")
    await engine.set_prompt(PROMPT_SHOT_26)
    await asyncio.sleep(1.5)

    # 5. Подсчет текущего числа карточек стоимости и плиток
    prev_cost_cards = await engine.count_cost_cards()
    initial_tiles = await engine.get_video_tiles_count()
    logger.info(f"Текущие счетчики: карточек={prev_cost_cards}, плиток={initial_tiles}")

    # 6. Отправка промпта
    logger.info("Отправка запроса в Veo...")
    await engine.submit_prompt()
    await asyncio.sleep(2.0)

    # 7. Ожидание карточки стоимости и подтверждение Genehmigen
    logger.info("Ожидание карточки стоимости Genehmigen...")
    card_found = await engine.wait_for_cost_card(previous_count=prev_cost_cards, timeout=30000)
    if card_found:
        logger.info("Карточка найдена! Нажатие Genehmigen...")
        approved = await engine.approve_last_card()
        logger.info(f"Результат нажатия Genehmigen: {approved}")
        if not approved:
            # Ручной поиск клика по option-row / button
            logger.info("Попытка прямого клика по селекторам Genehmigen...")
            btn = page.locator("[role='radio'][aria-label*='Genehmigen'], .option-row:has-text('Genehmigen'), button:has-text('Genehmigen')").last
            if await btn.count() > 0:
                await btn.click(force=True)
                logger.info("Прямой клик по Genehmigen успешен!")
    else:
        logger.warning("Карточка стоимости не появилась за 30с, проверяем кнопки...")
        btn = page.locator("[role='radio'][aria-label*='Genehmigen'], .option-row:has-text('Genehmigen'), button:has-text('Genehmigen')").last
        if await btn.count() > 0:
            await btn.click(force=True)
            logger.info("Genehmigen нажат запасным путем!")

    await page.screenshot(path="output/shot_26_costume_submitted.png")
    logger.info("Скриншот отправки сохранен в output/shot_26_costume_submitted.png")
    print("SUBMIT_SHOT_26_DONE")


if __name__ == "__main__":
    asyncio.run(main())
