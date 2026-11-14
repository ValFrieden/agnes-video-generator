import asyncio
import os
import sys
sys.path.insert(0, r"d:\Projects\VideoGenerator")
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
    page = await engine.connect()
    print("Connected to Flow via engine. Page URL:", page.url)
    
    ref_path = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\anatomical_fin_option_2.png"
    print("Attaching reference image:", ref_path)
    res = await engine.attach_reference_image(ref_path)
    print("Attach result:", res)
    await engine.close()

if __name__ == '__main__':
    asyncio.run(main())
