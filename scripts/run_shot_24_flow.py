import sys
import os
sys.path.insert(0, r"d:\Projects\VideoGenerator")
import asyncio
import logging
from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():
    engine = GoogleFlowEngine(
        cdp_url="http://127.0.0.1:9222",
        default_model="Veo 3.1 - Fast",
        default_resolution="720p",
        max_credits=20
    )
    
    prompt = (
        "High-angle aerial crane shot rising high above the glassy lake at dawn: "
        "breathtaking vast panorama of infinite serene morning nature, calm shoreline with weathered dark wood dock below, "
        "radiant liquid gold sunrise reflections shimmering on the water, boundless clear blue sky, pure tranquility, no humans."
    )
    ref_image = r"d:\Projects\VideoGenerator\references\panels_storyboard_06\panel_04_BR.png"
    out_clip = r"d:\Projects\VideoGenerator\output\shot_24_infinite_freedom.mp4"
    
    print("Starting generation in Google Flow...")
    success = await engine.generate_scene(
        prompt=prompt,
        reference_image_path=ref_image,
        output_clip_path=out_clip,
        style_suffix="Authentic 35mm optical cinema lens, Roger Deakins natural morning light, cinematic photorealism, 16:9 widescreen",
        skip_if_exists=False,
        max_retries=2
    )
    print(f"Generation result: {success}")
    await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
