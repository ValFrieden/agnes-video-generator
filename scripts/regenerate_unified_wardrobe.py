import asyncio
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, r"d:\Projects\VideoGenerator")

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_keys

valeri_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg"
woman_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_woman_portrait.jpg"
prism_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\prop_dream_prism.jpg"

output_dir = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"

STYLE = "Modern cinematic movie still, pristine 8k resolution, razor-sharp focus, crystal clear ARRI Alexa LF shot, perfect lighting, clean composition, rich cinematic contrast, no blur, no vintage grain, 16:9"

HEROINE_OUTFIT = "wearing a solid vibrant emerald-green silk midi dress with elegant 3/4 sleeves, clean solid emerald-green silk fabric, absolutely NO lilac accents, NO ribbons, NO contrasting belts"
VALERI_OUTFIT = "wearing a vintage distressed brown leather jacket over an olive-green button-up shirt and dark indigo trousers"

# We regenerate scenes 03, 04, 05, 07, 09, 10, 11 to have 100% unified wardrobe
scenes_prompts = {
    "03": {
        "prompt": f"{STYLE}, medium shot, Caucasian 40-year-old man Valeri {VALERI_OUTFIT}, strictly NO glasses, mouth closed, turns and sees Caucasian 32-year-old beautiful woman Elena with wavy chestnut hair, fair radiant skin, large expressive hazel eyes, {HEROINE_OUTFIT}, mouth closed, gentle subtle smile, standing under modern warm street illumination at evening boulevard, magical romantic connection",
        "refs": [valeri_ref]
    },
    "04": {
        "prompt": f"{STYLE}, medium two-shot, Caucasian man Valeri {VALERI_OUTFIT}, strictly NO glasses, mouth closed, and Caucasian woman Elena with wavy chestnut hair, {HEROINE_OUTFIT}, mouth closed, gentle affectionate gaze, standing close together on illuminated city avenue, light fresh evening breeze, crisp beautiful backlight, elegant cinematic framing",
        "refs": [valeri_ref]
    },
    "05": {
        "prompt": f"{STYLE}, close-up to medium shot, delicate hand of Caucasian woman Elena {HEROINE_OUTFIT} touching glowing brass crystal prism locket held by Caucasian man Valeri {VALERI_OUTFIT}, strictly NO glasses, mouth closed, radiant clean warm golden light illuminating their faces and emerald green and leather clothes, magical wonder, clean sharp focus",
        "refs": [valeri_ref]
    },
    "07": {
        "prompt": f"{STYLE}, medium full shot, Caucasian woman Elena {HEROINE_OUTFIT}, mouth closed, joyful radiant smile, twirling gracefully in gentle dance on open promenade, watched lovingly by Caucasian man Valeri {VALERI_OUTFIT}, strictly NO glasses, mouth closed, warm smile, crisp reflections on pavement",
        "refs": [woman_ref]
    },
    "09": {
        "prompt": f"{STYLE}, close-up, intertwined hands and warm smiling faces of Caucasian man Valeri {VALERI_OUTFIT} and Caucasian woman Elena {HEROINE_OUTFIT} holding glowing brass crystal prism locket, facets of crystal casting clean sharp golden rays of light across their clothes, mouth closed, deep emotional harmony, symbolic unity",
        "refs": [valeri_ref]
    },
    "10": {
        "prompt": f"{STYLE}, wide shot, slow morning sunrise, Caucasian man Valeri {VALERI_OUTFIT}, strictly NO glasses, mouth closed, and Caucasian woman Elena {HEROINE_OUTFIT}, mouth closed, standing side by side on panoramic rooftop terrace, watching glowing golden dawn sun rise over skyline of modern city, clean clear morning air, majestic inspiring vista",
        "refs": [valeri_ref]
    },
    "11": {
        "prompt": f"{STYLE}, wide shot with foreground focus, glowing brass crystal prism locket resting on clean smooth stone parapet in bright morning sunlight, in soft background Caucasian man Valeri {VALERI_OUTFIT}, strictly NO glasses, and Caucasian woman Elena {HEROINE_OUTFIT} walk away together hand-in-hand towards golden dawn, peaceful happy resolution",
        "refs": [prism_ref]
    }
}

negative_prompt = "lilac ribbons, lavender skirt, purple accents, black blouse, blue dress, beige dress, wedding gown, white dress, bare shoulders, strapless, vintage 90s grain, heavy film grain, noise, dust, scratches, blur, fuzzy, washed out, low contrast, sepia, edge code, film border, numbers on edge, Kodak numbers, text watermark, dark skin, African American, Black person, ethnicity drift, glasses, spectacles, eyewear, sunglasses, open mouth, talking, singing, visible teeth, lip-sync, warped face, extra fingers, deformed hands, duplicate locket, CGI 3D cartoon"

async def main():
    keys = get_api_keys()
    if not keys:
        print("No API keys found!")
        return
    api = AgnesImageAPI(api_key=keys[0])
    print("=== Regenerating Scenes 03, 04, 05, 07, 09, 10, 11 with 100% Unified Wardrobe ===")
    
    for scene_id, data in sorted(scenes_prompts.items()):
        target_path = os.path.join(output_dir, f"scene_{scene_id}.png")
        print(f"\n[Scene {scene_id}] Generating with solid emerald dress & leather jacket...")
        try:
            valid_refs = [r for r in data["refs"] if os.path.exists(r)]
            res = await api.generate_single_image(
                prompt=data["prompt"],
                reference_image_paths=valid_refs[:1] if valid_refs else None,
                size="1024x576", # 16:9
                negative_prompt=negative_prompt
            )
            await res.save(target_path)
            print(f"[Scene {scene_id}] SAVED: {target_path}")
        except Exception as e:
            print(f"[Scene {scene_id}] ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
