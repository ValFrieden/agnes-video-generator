import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from core.api.google_flow_engine import GoogleFlowEngine

async def check():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    
    # 1. Click flow-video-tile
    opened = await page.evaluate("""(() => {
        const tiles = document.querySelectorAll('flow-video-tile');
        if (tiles.length > 0) {
            tiles[0].click();
            return true;
        }
        return false;
    })()""")
    print("Opened flow-video-tile:", opened)
    await asyncio.sleep(2.5)
    print("URL after opening:", page.url)

    # 2. Find download button
    btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
    if btn:
        print("Found download button:", await btn.get_attribute("aria-label"))
        await btn.click()
        await asyncio.sleep(1.5)

        # 3. List all text in document or overlay
        texts = await page.evaluate("""(() => {
            return Array.from(document.querySelectorAll('button, [role="menuitem"], flow-menu-item, div.mat-mdc-menu-content *'))
                .map(el => (el.innerText || '').trim())
                .filter(t => t.length > 0 && t.length < 50);
        })()""")
        print("Menu texts found:", set(texts))
        await page.screenshot(path="output/menu_dropdown_live.png")
    else:
        print("Download button not found!")
        await page.screenshot(path="output/no_download_button.png")

if __name__ == '__main__':
    asyncio.run(check())
