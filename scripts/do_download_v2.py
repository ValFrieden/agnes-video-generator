import asyncio
import os
import sys
sys.path.insert(0, r"d:\Projects\VideoGenerator")
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
    target = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_sharks_surface_v2.mp4"
    print("Calling engine.download_latest_video for target:", target)
    res = await engine.download_latest_video(target, resolution="720p", timeout_seconds=45)
    print("Download result:", res)
    await engine.close()

if __name__ == '__main__':
    asyncio.run(main())
