import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

async def main():
    api_key = get_api_key()
    client = AgnesImageAPI(api_key=api_key)
    
    prompt = (
        "2D hand-drawn anime animation in Makoto Shinkai CoMix Wave Films aesthetic. "
        "Cinematic full body wide shot, 16:9 aspect ratio. "
        "A romantic European city boulevard at twilight night, glowing antique wrought-iron street lamps casting golden light and luminous bokeh circles onto the wet cobblestones with reflections. "
        "The couple walks forward towards the camera arm-in-arm along the boulevard: "
        "Valeri (1.85m tall) is a mature Caucasian man (approx 38-40 years old) with short textured dark-brown hair, neat light stubble along his jawline and chin, gentle warm smile, closed mouth, NO glasses. Wearing a vintage brown leather jacket with collar, olive button-up shirt, dark straight trousers, and polished dark brown leather dress shoes. "
        "Elena (1.80m tall, just 5cm shorter than Valeri, her head reaches his eye level) is an elegant European woman with high cheekbones, long dark espresso-brown wavy hair flowing loose over both shoulders and down her back, radiant gentle smile. Wearing an emerald green silk midi dress and elegant closed-toe high-heel pumps. STRICTLY NO sandals, NO flip-flops, NO bare feet! "
        "Elena gently holds Valeri's arm as they walk forward together in complete harmony, looking tenderly at each other. "
        "Pristine crystal clear digital hand-drawn 2D Japanese anime animation, razor-sharp clean linework, smooth cel shading, vibrant rich colors, zero noise, zero grain, masterpiece."
    )
    
    ref_paths = [
        r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_character_valeri.png",
        r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_character_elena.png",
        r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\couple_anime_scale_master_185_180.png",
        r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_06.png"
    ]
    valid_refs = [p for p in ref_paths if os.path.exists(p)]
    print(f"Using {len(valid_refs)} reference images: {valid_refs}")
    
    for i in range(2):
        print(f"Generating candidate {i+1}...")
        try:
            out = await client.generate_single_image(
                prompt=prompt,
                reference_image_paths=valid_refs,
                size="1280x720"
            )
            target = rf"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_06_candidate_{i+1}.png"
            await out.save(target)
            print(f"Saved candidate {i+1} to {target}")
        except Exception as e:
            print(f"Error on candidate {i+1}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
