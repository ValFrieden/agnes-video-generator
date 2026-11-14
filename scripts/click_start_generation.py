import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from core.api.google_flow_engine import GoogleFlowEngine

async def trigger():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    print("Connected. URL:", page.url)

    # Click 'Immer genehmigen' or 'Genehmigen'
    options = await page.query_selector_all("[aria-label*='Immer genehmigen'], [aria-label*='Genehmigen']")
    print(f"Found {len(options)} genehmigen options")
    for opt in options:
        try:
            if await opt.is_visible():
                await opt.click(force=True)
                print("Clicked option:", await opt.get_attribute('aria-label'))
                break
        except Exception as e:
            print("Error clicking option:", e)

    await asyncio.sleep(1.0)

    # Click 'Generierung starten'
    start_btn = await page.query_selector("[aria-label*='Generierung starten'], button:has-text('Generierung starten'), [aria-label*='Start generation']")
    if start_btn:
        print("Found start button, clicking...")
        await start_btn.click(force=True)
        print("Clicked start button!")
    else:
        # maybe arrow_forward button
        arrow_btn = await page.query_selector("button:has-text('arrow_forward')")
        if arrow_btn:
            print("Found arrow_forward button, clicking...")
            await arrow_btn.click(force=True)

    await asyncio.sleep(3.0)
    await page.screenshot(path="output/flow_after_start_clicked.png")
    print("Screenshot saved to output/flow_after_start_clicked.png")

if __name__ == '__main__':
    asyncio.run(trigger())
