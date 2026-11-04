import asyncio
import os
import sys

sys.path.insert(0, r"d:\Projects\VideoGenerator")

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_keys

valeri_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg"
woman_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_woman_portrait.jpg"
output_dir = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"

STYLE = "Modern high-end cinematic movie still, pristine 8k ARRI Alexa LF cinematography, crystal clear razor-sharp focus, natural cinematic lighting, rich depth of field, NO blur, NO vintage grain, NO film borders, clean composition, casual modern clothing, 16:9"

test_prompts = {
    "test_man_casual": {
        "prompt": f"{STYLE}, medium portrait shot, handsome Caucasian man exactly matching the reference photo face (Valeri), dark brown textured hair, expressive hazel-gray eyes, neat stubble, wearing casual modern navy blue crewneck sweater and dark casual jacket, strictly NO wedding suit, NO tie, strictly NO glasses, mouth gently closed, evening modern city cafe background with warm bokeh",
        "ref": valeri_ref
    },
    "test_woman_casual": {
        "prompt": f"{STYLE}, medium portrait shot, beautiful Caucasian woman exactly matching the reference photo face, chestnut brown hair worn down in natural soft waves, warm radiant smile with gentle closed mouth, elegant hazel eyes, wearing casual modern emerald-green cashmere knit sweater, strictly NO wedding dress, NO bridal veil, NO tiara, modern sunlit urban promenade background",
        "ref": woman_ref
    },
    "test_couple_casual": {
        "prompt": f"{STYLE}, medium two-shot, the couple from the reference photos standing together on a modern evening river embankment, handsome Caucasian man in casual navy jacket and the beautiful Caucasian woman in casual emerald sweater, smiling lovingly at each other, mouth closed, strictly NO wedding attire, clean crisp modern cinema",
        "ref": valeri_ref
    }
}

negative = "wedding dress, bridal gown, veil, tiara, wedding suit, tuxedo, necktie, flowers, bouquet, bride, groom, marriage ceremony, vintage grain, blur, noise, text, watermark, glasses, sunglasses, deformed, dark skin, African American"

async def main():
    keys = get_api_keys()
    api = AgnesImageAPI(api_key=keys[0])
    print("=== Generating Casual Lookdev Samples from Real Hochzeit Faces ===")
    
    for name, data in test_prompts.items():
        out_path = os.path.join(output_dir, f"{name}.png")
        print(f"Generating {name}...")
        try:
            res = await api.generate_single_image(
                prompt=data["prompt"],
                reference_image_paths=[data["ref"]],
                size="1024x576",
                negative_prompt=negative
            )
            await res.save(out_path)
            print(f"SAVED: {out_path}")
        except Exception as e:
            print(f"ERROR {name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
