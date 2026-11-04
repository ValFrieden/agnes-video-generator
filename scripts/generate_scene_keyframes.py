import asyncio
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, r"d:\Projects\VideoGenerator")

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_keys

valeri_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\valeri_turnaround.jpg"
elena_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\elena_turnaround.jpg"
prism_ref = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\prop_dream_prism.jpg"

output_dir = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"

# Modern, clean, crisp cinematic style WITHOUT 90s grain or blur
STYLE = "Modern cinematic movie still, pristine 8k resolution, razor-sharp focus, crystal clear ARRI Alexa LF shot, perfect lighting, clean composition, rich cinematic contrast, no blur, no vintage grain, 16:9"

scenes_prompts = {
    "01": {
        "prompt": f"{STYLE}, wide shot, Caucasian 40-year-old handsome man named Valeri with short textured dark-brown hair, light neat designer stubble, warm expressive hazel-gray eyes, small distinct mole on cheek, wearing clean brown leather jacket over olive-green shirt and dark trousers, strictly NO glasses, mouth closed, walking along clean modern illuminated evening city river promenade, holding small brass crystal locket in his hand, reflections of warm city lights on water, calm introspective mood",
        "refs": [valeri_ref, prism_ref]
    },
    "02": {
        "prompt": f"{STYLE}, medium shot, Caucasian 40-year-old handsome man named Valeri with short textured dark-brown hair, light neat designer stubble, hazel-gray eyes, small mole on cheek, wearing brown leather jacket over olive-green shirt, strictly NO glasses, mouth gently closed, standing near glowing panoramic glass window of a modern cozy cafe, holding antique brass crystal locket in his open palm, soft warm background bokeh, thoughtful longing look",
        "refs": [valeri_ref, prism_ref]
    },
    "03": {
        "prompt": f"{STYLE}, medium shot, Caucasian 40-year-old man Valeri in brown leather jacket and olive shirt, strictly NO glasses, mouth closed, turns and sees Caucasian 32-year-old beautiful woman Elena with wavy chestnut hair, fair radiant skin, large expressive emerald-green eyes, wearing elegant emerald and lavender silk dress, mouth closed, gentle subtle smile, standing under modern warm street illumination at evening boulevard, magical romantic connection",
        "refs": [valeri_ref, elena_ref]
    },
    "04": {
        "prompt": f"{STYLE}, medium two-shot, Caucasian man Valeri in brown leather jacket and olive shirt, strictly NO glasses, mouth closed, and Caucasian woman Elena in emerald-lavender silk dress, mouth closed, gentle affectionate gaze, standing close together on illuminated city avenue, light fresh evening breeze, crisp beautiful backlight, elegant cinematic framing",
        "refs": [valeri_ref, elena_ref]
    },
    "05": {
        "prompt": f"{STYLE}, close-up to medium shot, delicate hand of Caucasian woman Elena touching the glowing brass crystal prism locket held by Caucasian man Valeri, strictly NO glasses, mouth closed, radiant clean warm golden light illuminating their faces and hands, magical wonder, clean sharp focus",
        "refs": [valeri_ref, elena_ref, prism_ref]
    },
    "06": {
        "prompt": f"{STYLE}, dynamic wide cinematic shot, Caucasian man Valeri in brown leather jacket, strictly NO glasses, mouth closed, walking hand-in-hand with Caucasian woman Elena in emerald silk dress, mouth closed, joyful radiant expression, along illuminated evening boulevard with glowing artistic city installations, warm ambient light, pure happiness",
        "refs": [valeri_ref, elena_ref]
    },
    "07": {
        "prompt": f"{STYLE}, medium full shot, Caucasian woman Elena in elegant flowing emerald silk dress, mouth closed, joyful radiant smile, twirling gracefully in gentle dance on open promenade, watched lovingly by Caucasian man Valeri in brown leather jacket, strictly NO glasses, mouth closed, warm smile, crisp reflections on pavement",
        "refs": [elena_ref, valeri_ref]
    },
    "08": {
        "prompt": f"{STYLE}, medium close-up, Caucasian 40-year-old man Valeri with short dark-brown hair, neat stubble, expressive hazel-gray eyes, small mole on cheek, wearing brown leather jacket over olive shirt, strictly NO glasses, mouth closed, deeply touched loving expression, warm golden light gently illuminating his face, crisp cinematic portrait",
        "refs": [valeri_ref]
    },
    "09": {
        "prompt": f"{STYLE}, macro close-up, intertwined hands of Caucasian man Valeri and Caucasian woman Elena holding glowing brass crystal prism locket, facets of crystal casting clean sharp golden rays of light across their clothes, mouth closed, deep emotional harmony, symbolic unity",
        "refs": [valeri_ref, elena_ref, prism_ref]
    },
    "10": {
        "prompt": f"{STYLE}, wide shot, slow morning sunrise, Caucasian man Valeri, strictly NO glasses, mouth closed, and Caucasian woman Elena in silk dress, mouth closed, standing side by side on panoramic rooftop terrace, watching glowing golden dawn sun rise over skyline of modern city, clean clear morning air, majestic inspiring vista",
        "refs": [valeri_ref, elena_ref]
    },
    "11": {
        "prompt": f"{STYLE}, wide shot with foreground focus, glowing brass crystal prism locket resting on clean smooth stone parapet in bright morning sunlight, in soft background Caucasian man Valeri, strictly NO glasses, and Caucasian woman Elena walk away together hand-in-hand towards golden dawn, peaceful happy resolution",
        "refs": [prism_ref, valeri_ref, elena_ref]
    }
}

negative_prompt = "vintage 90s grain, heavy film grain, noise, dust, scratches, blur, fuzzy, washed out, low contrast, sepia, edge code, film border, numbers on edge, Kodak numbers, text watermark, dark skin, African American, Black person, ethnicity drift, glasses, spectacles, eyewear, sunglasses, open mouth, talking, singing, visible teeth, lip-sync, warped face, extra fingers, deformed hands, duplicate locket, CGI 3D cartoon"

async def main():
    keys = get_api_keys()
    if not keys:
        print("No API keys found!")
        return
    api = AgnesImageAPI(api_key=keys[0])
    print("=== Generating Clean Modern Cinematic Keyframes (Scenes 01-11) ===")
    
    for scene_id, data in scenes_prompts.items():
        target_path = os.path.join(output_dir, f"scene_{scene_id}.png")
        print(f"\n[Scene {scene_id}] Generating reference keyframe...")
        try:
            valid_refs = [r for r in data["refs"] if os.path.exists(r)]
            res = await api.generate_single_image(
                prompt=data["prompt"],
                reference_image_paths=valid_refs[:1],
                size="1024x576", # 16:9
                negative_prompt=negative_prompt
            )
            await res.save(target_path)
            print(f"[Scene {scene_id}] SAVED: {target_path}")
        except Exception as e:
            print(f"[Scene {scene_id}] ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
