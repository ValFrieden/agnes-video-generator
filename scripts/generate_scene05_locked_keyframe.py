import asyncio
import os
import sys

sys.path.insert(0, r"d:\Projects\VideoGenerator")

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_keys

output_path = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_05_locked.png"
ref_anchor = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\UNIFIED_CANON_ANCHOR_REF.png"

prompt = (
    "Makoto Shinkai CoMix Wave Films anime aesthetic, high-end 2D digital hand-drawn animation, pristine sharp clean line art. "
    "Inside an elegant room standing right next to a wide panoramic bay window overlooking a golden city skyline during a warm golden sunset. "
    "The couple must exactly match the reference image: "
    "1. The man (Valeri) must strictly replicate the reference face: short textured dark brown hair with messy natural forehead bangs, defined masculine jawline with neat stubble, straight nose, mouth closed, wearing the vintage brown leather jacket with patch pockets over an olive button-down shirt. "
    "2. The woman (Elena) must strictly replicate the reference face and hair: long deep dark espresso brown wavy hair flowing loose over both shoulders and down her back, identical dark brown hair color matching the reference, gentle sweet smile with mouth closed, wearing the emerald green silk midi dress. "
    "They are tenderly embracing each other by the window, warm amber sunset sunlight and soft sunbeams streaming through the glass. "
    "Cinematic warm romantic atmosphere, 16:9, masterpiece, crystal clear, vibrant colors, pristine 2D anime art."
)

negative = (
    "different face, generic anime face, round childish face, puffy hair, swept up hair, side-parted hair, "
    "light brown hair, reddish hair, chestnut highlights, blonde, bun, updo, tied hair, hair in bun, ponytail, "
    "hairclip, short hair, bob cut, clapperboard, slate, text, watermark, subtitles, open mouth, teeth, "
    "singing, shouting, glasses, sunglasses, vintage grain, noise, film grain, analog grain, scratches, "
    "dust, 3d, cgi, render, photo, photorealistic, live action, deformed hands, extra fingers, dark skin"
)

async def main():
    keys = get_api_keys()
    api = AgnesImageAPI(api_key=keys[0])
    print("Generating Scene 05 with locked Valeri face & Elena dark wavy hair...")
    res = await api.generate_single_image(
        prompt=prompt,
        reference_image_paths=[ref_anchor],
        size="1280x720",
        negative_prompt=negative
    )
    await res.save(output_path)
    print(f"SUCCESS: Saved {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
