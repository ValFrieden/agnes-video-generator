import asyncio
import os
import sys

sys.path.insert(0, r"d:\Projects\VideoGenerator")

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_keys

output_path = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_04_locked.png"
ref_anchor = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\UNIFIED_CANON_ANCHOR_REF.png"

prompt = (
    "Makoto Shinkai CoMix Wave Films anime aesthetic, high-end 2D digital hand-drawn animation, pristine sharp clean line art. "
    "Full body wide shot, 16:9 aspect ratio. "
    "On an atmospheric cozy illuminated cobblestone street lined with warm glowing lanterns, street lamps, and fallen autumn leaves scattered on the pavement, "
    "the couple walks forward side by side holding hands. "
    "The couple must strictly replicate the reference image UNIFIED_CANON_ANCHOR_REF: "
    "1. The man (Valeri, 1.85m tall) must strictly replicate the reference face from panel 1 and 2: short textured dark brown hair with messy natural forehead bangs, defined mature European masculine jawline with neat stubble, straight nose, mouth closed with gentle pleasant smile, wearing the vintage brown leather jacket with patch pockets over an olive button-down shirt, dark jeans, and classic brown leather shoes. NO glasses. "
    "2. The woman (Elena, 1.80m tall, reaching Valeri's eye level) must strictly replicate the reference face and hair from panel 3: long deep dark espresso brown wavy hair flowing loose over both shoulders and down her back, high cheekbones, gentle sweet smile with mouth closed, wearing the pure emerald green silk midi dress and elegant closed-toe high-heel pumps. "
    "They share a warm affectionate glance as they stroll forward together holding hands along the glowing evening boulevard. "
    "Cinematic warm amber bokeh lantern glow, 16:9, masterpiece, crystal clear, vibrant rich colors, pristine 2D anime art, zero noise, zero grain."
)

negative = (
    "different face, generic anime face, round childish face, teenager face, boyish face, puffy hair, swept up hair, side-parted hair, "
    "light brown hair, reddish hair, chestnut highlights, blonde, bun, updo, tied hair, hair in bun, ponytail, "
    "hairclip, short hair, bob cut, clapperboard, slate, text, watermark, subtitles, open mouth, teeth, "
    "singing, shouting, glasses, sunglasses, vintage grain, noise, film grain, analog grain, scratches, "
    "dust, 3d, cgi, render, photo, photorealistic, live action, deformed hands, extra fingers, bare feet, sandals, flip flops, slippers, sneakers"
)

async def main():
    keys = get_api_keys()
    api = AgnesImageAPI(api_key=keys[0])
    print("Generating Scene 04 with locked Valeri & Elena canonical faces via UNIFIED_CANON_ANCHOR_REF...")
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
