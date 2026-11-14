import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    print("Connected. Approving cost card...")
    ok = await engine.approve_cost_card()
    print("engine.approve_cost_card() ->", ok)
    if not ok:
        btn = page.locator("[role='radio'][aria-label*='Genehmigen'], .option-row:has-text('Genehmigen'), button:has-text('Genehmigen')").last
        if await btn.count() > 0:
            await btn.click(force=True)
            print("Direct click on Genehmigen succeeded!")
    
    await asyncio.sleep(2.0)
    await page.screenshot(path="output/genehmigen_approved_state.png")
    print("Screenshot saved to output/genehmigen_approved_state.png")

if __name__ == "__main__":
    asyncio.run(main())
