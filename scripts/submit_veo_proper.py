"""scripts/submit_veo_proper.py — Точная отправка видео в Veo 3.1 с префиксом 'Generate video with Veo:'."""

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
logger = logging.getLogger("SubmitVeoProper")

CHAR_REF = Path("references/character_valeri_live_action.jpg").resolve()
STYLE_REF = Path("references/kling_style_anchors/anchor_01_wet_dock_macro.png").resolve()

# Ключевое отличие: явный префикс 'Generate video with Veo:'
PROMPT = (
    "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, "
    "authentic human actor. A 42-year-old Caucasian man with short neat dark brown hair and subtle stubble beard "
    "sitting at a rustic wooden table in a paper-walled room, wearing a vintage slate tweed jacket "
    "over a dark linen shirt, no eyeglasses, lips closed. He picks up a flat 2D cardboard cutout "
    "coffee cup, looks at it with sarcastic bemusement, taps his finger against the flat paper surface "
    "showing it is fake props, real tactile textures, warm morning sunlight, master cinematography, "
    "16:9 widescreen, no cartoon, no animation, no 2D, no CGI"
)


async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()

    logger.info("Очистка поля ввода...")
    await engine.clear_prompt()

    logger.info("Прикрепление фото живого актёра...")
    await engine.attach_reference_image(str(CHAR_REF))

    logger.info("Прикрепление якоря стиля...")
    await engine.attach_reference_image(str(STYLE_REF))

    logger.info("Ввод промпта для Veo...")
    await engine.set_prompt(PROMPT)
    await asyncio.sleep(1.0)

    # Скриншот перед кликом
    await page.screenshot(path="output/veo_before_submit.png")

    logger.info("Отправка запроса в Veo...")
    await engine.submit_prompt()
    await asyncio.sleep(3.0)

    # Проверка ответа агента
    logger.info("Ожидание карточки стоимости или ответа...")
    res = await page.evaluate("""() => {
        const text = document.body.innerText;
        const match = text.match(/Das kostet (\\d+) Guthabenpunkte/);
        const approveBtn = !!document.querySelector('button[aria-label*="Genehmigen"], button[aria-label*="Approve"]');
        return {
            costMatch: match ? match[0] : null,
            hasApproveBtn: approveBtn,
            lastSnippet: text.slice(-400)
        };
    }""")
    logger.info(f"Статус после отправки: {res}")

    # Если есть кнопка Genehmigen, нажимаем
    btn = page.locator('button:has-text("Genehmigen"), button:has-text("Approve")').last
    if await btn.count() > 0 and await btn.is_visible():
        logger.info("Нажатие кнопки Genehmigen...")
        await btn.click()
        logger.info("Кнопка Genehmigen нажата!")
        await asyncio.sleep(2.0)

    await page.screenshot(path="output/veo_submitted_state.png")
    logger.info("Скриншот сохранён: output/veo_submitted_state.png")
    print("SUBMIT_DONE")


if __name__ == "__main__":
    asyncio.run(main())
