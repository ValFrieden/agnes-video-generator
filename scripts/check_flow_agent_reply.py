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

    await asyncio.sleep(2.0)
    await page.screenshot(path="output/flow_agent_latest.png")
    print("Screenshot saved to output/flow_agent_latest.png")

    body = await page.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    print("LATEST 30 LINES OF TEXT:")
    for l in lines[-30:]:
        print(" ", l)


if __name__ == "__main__":
    asyncio.run(main())
