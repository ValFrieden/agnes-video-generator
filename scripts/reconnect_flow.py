import asyncio
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"


async def main():
    engine = GoogleFlowEngine(downloads_dir=str(Path("output").resolve()))
    page = await engine.connect()

    if PROJECT_URL not in page.url:
        print(f"Navigating to project: {PROJECT_URL}...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(4.0)

    print("Current URL:", page.url)
    await page.screenshot(path="output/flow_project_reconnected.png")

    tiles_info = await page.evaluate("""() => {
        const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
        return tiles.map((t, idx) => ({
            index: idx,
            text: (t.innerText || '').slice(0, 100),
            hasVideo: !!t.querySelector('video'),
            hasImg: !!t.querySelector('img')
        }));
    }""")
    print("Tiles count:", len(tiles_info))
    print("Tiles detail:", tiles_info)


if __name__ == "__main__":
    asyncio.run(main())
