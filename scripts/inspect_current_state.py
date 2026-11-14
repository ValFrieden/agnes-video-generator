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

    await page.screenshot(path="output/current_screen_now.png")
    print("URL:", page.url)

    state = await page.evaluate("""() => {
        return {
            title: document.title,
            hasVideo: !!document.querySelector('video'),
            videoSrc: document.querySelector('video') ? document.querySelector('video').src : null,
            bodyText: document.body.innerText.slice(0, 1500),
            editorOpen: window.location.href.includes('/edit/'),
            backButtonVisible: !!document.querySelector('button[aria-label*="arrow_back"], button[aria-label*="Back"], button:has-text("arrow_back")'),
        };
    }""")
    for k, v in state.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
