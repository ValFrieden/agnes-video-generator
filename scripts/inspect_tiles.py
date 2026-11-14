import asyncio
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine


async def main():
    engine = GoogleFlowEngine(downloads_dir=str(Path("output").resolve()))
    page = await engine.connect()

    # Сделать скриншот холста для визуальной проверки
    await page.screenshot(path="output/flow_canvas_shot25_live.png")
    print("Screenshot saved to output/flow_canvas_shot25_live.png")

    tiles_info = await page.evaluate("""() => {
        const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
        return tiles.map((t, idx) => ({
            index: idx,
            text: t.innerText.slice(0, 100),
            hasVideo: !!t.querySelector('video'),
            hasImg: !!t.querySelector('img')
        }));
    }""")
    print("Tiles info:", tiles_info)


if __name__ == "__main__":
    asyncio.run(main())
