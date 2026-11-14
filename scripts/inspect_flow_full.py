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

    await page.screenshot(path="output/flow_screen_live.png", full_page=False)
    print("Screenshot saved to output/flow_screen_live.png")

    info = await page.evaluate("""() => {
        const bubbles = Array.from(document.querySelectorAll('flow-chat-bubble, .chat-message, [role="log"] *'));
        const lastBubbles = bubbles.slice(-5).map(b => b.innerText || '');
        const promptInput = document.querySelector('textarea, [contenteditable="true"], input[type="text"]');
        const promptVal = promptInput ? (promptInput.value || promptInput.innerText) : null;
        const chips = Array.from(document.querySelectorAll('flow-chip, [role="button"] img, .chip'));
        const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
        const bodyText = document.body.innerText.slice(0, 1000);
        return {
            url: window.location.href,
            tilesCount: tiles.length,
            promptVal: promptVal ? promptVal.slice(0, 200) : null,
            chipsCount: chips.length,
            lastBubbles: lastBubbles,
            bodySnippet: bodyText
        };
    }""")
    print("PAGE INFO:")
    for k, v in info.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
