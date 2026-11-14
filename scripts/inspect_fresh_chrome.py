import asyncio
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine


async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()

    print("Current URL:", page.url)
    await page.screenshot(path="output/chrome_fresh_launch.png")
    print("Screenshot saved to output/chrome_fresh_launch.png")

    # Если URL содержит /edit/, выходим из редактора
    if "/edit/" in page.url:
        print("Detected /edit/ in URL. Clicking Done / Fertig to return to canvas...")
        await page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const fertig = btns.find(b => (b.innerText || '').trim() === 'Fertig' || (b.innerText || '').trim() === 'Done');
            if (fertig) fertig.click();
        }""")
        await asyncio.sleep(2.0)
        print("URL after exiting editor:", page.url)

    # Проверим, что на холсте
    tiles = await page.evaluate("() => document.querySelectorAll('flow-video-tile').length")
    print("Video tiles on canvas:", tiles)


if __name__ == "__main__":
    asyncio.run(main())
