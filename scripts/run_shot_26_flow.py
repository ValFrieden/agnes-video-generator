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
    
    # Connect and ensure we are on the canvas, not in editor
    page = await engine.connect()
    if "/edit/" in page.url:
        canvas_url = page.url.split("/edit/")[0]
        print(f"Exiting editor back to canvas: {canvas_url}")
        await page.goto(canvas_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)
    
    prompt = (
        "Extreme macro slow-motion cinematography: a single pristine, spherical morning dewdrop resting delicately "
        "on the edge of a wild flower petal. Perfectly reflected inside the clear dewdrop is the blazing golden dawn sun "
        "and serene lake horizon. A soft morning breeze makes the dewdrop gently tremble, casting sparkling light refractions "
        "and microscopic golden flares. In the deep creamy bokeh background, golden morning water ripples glow softly. "
        "Pure tranquility, 35mm optical cinema lens, photorealistic macro, no humans."
    )
    
    ref_image_1 = r"d:\Projects\VideoGenerator\references\kling_style_anchors\anchor_01_wet_dock_macro.png"
    ref_image_2 = r"d:\Projects\VideoGenerator\references\kling_style_anchors\anchor_03_liquid_gold_sun.png"
    out_clip = r"d:\Projects\VideoGenerator\output\shot_26_dew_reflection_sun.mp4"
    
    print("Generating Shot 26 in Google Flow Veo 3.1...")
    success = await engine.generate_scene(
        prompt=prompt,
        reference_image_path=ref_image_1,
        extra_references=[ref_image_2],
        output_clip_path=out_clip,
        style_suffix="Authentic 35mm optical cinema lens, Roger Deakins natural morning light, cinematic photorealism, 16:9 widescreen",
        skip_if_exists=False,
        max_retries=2
    )
    print(f"Shot 26 Generation result: {success}")
    await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
