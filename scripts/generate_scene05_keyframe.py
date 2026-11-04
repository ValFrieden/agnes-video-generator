import asyncio
import os
import sys

sys.path.insert(0, r"d:\Projects\VideoGenerator")

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_keys

output_path = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_05_fixed.png"
ref_couple = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_04.png"

prompt = (
    "Makoto Shinkai CoMix Wave Films anime aesthetic, high-end 2D digital hand-drawn animation, pristine sharp clean line art. "
    "Inside an elegant sunlit room standing next to a large panoramic bay window overlooking a golden city skyline during a warm golden sunset. "
    "A romantic anime couple: handsome Caucasian man (Valeri) with short textured dark brown hair, light neat stubble, wearing a vintage brown leather jacket over an olive collared shirt, mouth closed, no glasses. "
    "Beside him is a beautiful Caucasian woman (Elena) with long loose dark brown wavy hair flowing over her shoulders and down her back, wearing an elegant emerald green silk midi dress, mouth closed with a gentle sweet smile. "
    "They are tenderly embracing each other by the window bathed in warm golden sunset light and soft god rays. "
    "Cinematic warm amber atmosphere, vibrant colors, 16:9, masterpiece, pristine digital anime art."
)

negative = (
    "bun, updo, hair in bun, tied hair, ponytail, hairclip, clapperboard, slate, text, watermark, subtitles, "
    "open mouth, teeth, singing, shouting, glasses, sunglasses, vintage grain, noise, film grain, analog grain, "
    "scratches, dust, 3d, cgi, render, photo, photorealistic, live action, deformed hands, extra fingers, dark skin"
)

async def main():
    keys = get_api_keys()
    api = AgnesImageAPI(api_key=keys[0])
    print("Generating Scene 05 keyframe with loose wavy hair and emerald dress...")
    res = await api.generate_single_image(
        prompt=prompt,
        reference_image_paths=[ref_couple],
        size="1280x720",
        negative_prompt=negative
    )
    await res.save(output_path)
    print(f"SUCCESS: Saved {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
