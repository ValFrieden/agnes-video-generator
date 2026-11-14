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
        
        # Take screenshot of Flow page
        ss_path = r"d:\Projects\VideoGenerator\output\flow_home_screenshot.png"
        await page.screenshot(path=ss_path)
        print("Screenshot saved to:", ss_path)
        
        # Check text or projects visible
        content = await page.content()
        print("Page HTML size:", len(content))
        
        # List links or buttons
        buttons = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button, a')).map(el => (el.innerText || '').trim()).filter(Boolean);
        }""")
        print("Visible buttons/links:", buttons[:30])
    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
