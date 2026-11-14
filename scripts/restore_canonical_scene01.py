import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

async def main():
    api = AgnesImageAPI(api_key=get_api_key())
    out_file = Path("nikogda_ne_boyus_frames/scene_01.png")
    
    prompt = (
        "Cinematic wide establishing shot, open cargo ramp of a military transport plane flying above stormy thunderclouds at 10,000 feet. "
        "34-year-old rugged Caucasian man Valeri, athletic build, short matte brown hair, grey-green eyes, light stubble, "
        "dark graphite tactical overshirt billowing in cold high-altitude wind, distressed leather boots, steel compass pendant on neck, "
        "standing calmly on the very edge of the abyss with a peaceful confident smile, about to step backward into the clouds, "
        "cold indigo lighting, lightning flashes, 35mm film grain, authentic human skin pores, hyper-realistic, 16:9 widescreen"
    )
    
    print("Regenerating canonical scene_01.png with original rugged hero Valeri...")
    img = await api.generate_single_image(prompt=prompt, size="1344x768")
    await img.save(str(out_file))
    print(f"Restored canonical scene_01.png ({out_file.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
