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

    await page.screenshot(path="output/flow_debug_state.png", full_page=True)
    print("Screenshot saved to output/flow_debug_state.png")

    body = await page.evaluate("() => document.body.innerText")
    print("PAGE BODY SNIPPET (First 1500 chars):")
    print(body[:1500])
    print("---")
    print("PAGE BODY SNIPPET (Last 1500 chars):")
    print(body[-1500:])


if __name__ == "__main__":
    asyncio.run(main())
