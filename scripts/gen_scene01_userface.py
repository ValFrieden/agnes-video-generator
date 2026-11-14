import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

async def main():
    api = AgnesImageAPI(api_key=get_api_key())
    out_file = Path("nikogda_ne_boyus_frames/scene_01.png")
    ref_face = Path("nikogda_ne_boyus_frames/valeri_ref_front.jpg")
    
    prompt = (
        "Cinematic wide establishing shot, open cargo ramp of a military transport plane flying above stormy thunderclouds at 10,000 feet. "
        "The man from reference image Valeri, athletic build, short dark hair, dark tactical overshirt, steel compass pendant on neck, "
        "standing calmly on the very edge of the cargo bay door with a peaceful confident smile, about to take a fearless step backward into the clouds, "
        "cold indigo lighting, distant lightning flashes, authentic human skin pores, hyper-realistic, 35mm film, 16:9 widescreen"
    )
    
    print(f"Generating scene_01.png with reference face: {ref_face}...")
    img = await api.generate_single_image(
        prompt=prompt,
        reference_image_paths=[str(ref_face.resolve())],
        size="1344x768"
    )
    await img.save(str(out_file))
    print(f"Saved updated scene_01.png ({out_file.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
