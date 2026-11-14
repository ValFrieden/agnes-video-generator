import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from core.api.google_flow_engine import GoogleFlowEngine

async def debug_menu():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    print("Page URL:", page.url)

    # If we are on canvas or /edit/, see where we are
    btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
    if not btn:
        print("No direct download button. Looking for video tile...")
        tile = await page.query_selector("button:has(video), [role='button']:has(video)")
        if tile:
            print("Clicking video tile to open editor...")
            await tile.click(force=True)
            await asyncio.sleep(3.0)
            btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')

    if btn:
        print("Clicking download button:", await btn.get_attribute("aria-label"))
        await btn.click(force=True)
        await asyncio.sleep(1.5)

        # Print all visible menu items
        items = await page.query_selector_all('button, [role="menuitem"], flow-menu-item, .mat-mdc-menu-item')
        print(f"Total potential menu items: {len(items)}")
        for it in items:
            t = (await it.text_content() or "").strip()
            vis = await it.is_visible()
            if vis and len(t) < 40:
                print(f"Visible menu item: {t!r}")

        await page.screenshot(path="output/debug_download_menu.png")
        print("Saved debug screenshot to output/debug_download_menu.png")

if __name__ == '__main__':
    asyncio.run(debug_menu())
