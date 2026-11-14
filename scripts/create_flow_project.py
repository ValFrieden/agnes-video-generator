import sys
import os
sys.path.insert(0, r"d:\Projects\VideoGenerator")
import asyncio
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
    try:
        page = await engine.connect()
        print("URL:", page.url)

        # Check existing project cards
        cards = await page.evaluate("""() => {
            const projectCards = Array.from(document.querySelectorAll('a[href*="/project/"], div[role="button"]'));
            return projectCards.map(c => ({
                text: (c.innerText || '').trim(),
                href: c.getAttribute('href') || ''
            })).filter(x => x.text || x.href);
        }""")
        print("Found project cards:", cards)
        
        # Click "Neues Projekt" to create or open our project
        new_proj_btn = page.locator("button:has-text('Neues Projekt'), button:has-text('New project')").first
        if await new_proj_btn.is_visible():
            print("Clicking 'Neues Projekt'...")
            await new_proj_btn.click()
            await asyncio.sleep(4)
            print("Current URL after click:", page.url)
            
            # Wait for project canvas to load
            await page.screenshot(path=r"d:\Projects\VideoGenerator\output\flow_project_canvas.png")
            print("Canvas screenshot saved!")
        else:
            print("'Neues Projekt' button not visible directly.")
    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
