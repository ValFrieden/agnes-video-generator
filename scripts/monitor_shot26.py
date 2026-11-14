import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import time
from core.api.google_flow_engine import GoogleFlowEngine

async def monitor_and_download():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    print("Connected. URL:", page.url)

    # Let's count current video elements / tiles
    initial_tiles = await page.query_selector_all("button:has(video), [role='button']:has(video), .tile:has(video)")
    print(f"Initial video tiles count: {len(initial_tiles)}")

    # We wait up to 400 seconds for generation to complete
    start_time = time.time()
    while time.time() - start_time < 400:
        await asyncio.sleep(10.0)
        # Check for progress indicators
        spinners = await page.query_selector_all("mat-progress-spinner, mat-progress-bar, [role='progressbar'], .generating")
        current_tiles = await page.query_selector_all("button:has(video), [role='button']:has(video), .tile:has(video)")
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed}s] Video tiles: {len(current_tiles)}, Spinners/Progress: {len(spinners)}")

        # Check if there is a newly completed tile or new video
        if len(current_tiles) > len(initial_tiles) and len(spinners) == 0:
            print("New video tile completed! Waiting 5s before inspecting...")
            await asyncio.sleep(5.0)
            break

    await page.screenshot(path="output/flow_shot26_generation_done.png")
    print("Screenshot saved to output/flow_shot26_generation_done.png")

if __name__ == '__main__':
    asyncio.run(monitor_and_download())
