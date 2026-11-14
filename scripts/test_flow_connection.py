import sys
import os
sys.path.insert(0, r"d:\Projects\VideoGenerator")
import asyncio
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
    try:
        page = await engine.connect()
        print("Connected to Flow page URL:", page.url)
        title = await page.title()
        print("Page Title:", title)
    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
