import asyncio
import json
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"


async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()

    print("Current URL before nav:", page.url)
    print("Navigating back to main project canvas:", PROJECT_URL)
    await page.goto(PROJECT_URL, wait_until="domcontentloaded")
    await asyncio.sleep(4.0)
    print("Current URL after nav:", page.url)

    await page.screenshot(path="output/canvas_restored_clean.png")

    canvas_info = await page.evaluate("""() => {
        const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
        return {
            tilesCount: tiles.length,
            tilesDetails: tiles.map((t, idx) => ({
                index: idx,
                text: (t.innerText || '').slice(0, 150),
                hasVideo: !!t.querySelector('video'),
                hasImg: !!t.querySelector('img'),
                videoSrc: t.querySelector('video') ? t.querySelector('video').src : null,
                imgSrc: t.querySelector('img') ? t.querySelector('img').src : null
            }))
        };
    }""")
    print("CANVAS TILES INFO:")
    print(json.dumps(canvas_info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
