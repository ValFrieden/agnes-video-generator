import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

async def main():
    api_key = get_api_key()
    api = AgnesImageAPI(api_key=api_key)
    out_dir = Path("nikogda_ne_boyus_frames")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "character_front.png"
    
    prompt = (
        "Character design reference portrait, front view close-up of 34-year-old rugged Caucasian man Valeri, "
        "short matte brown textured hair, piercing grey-green eyes, well-groomed light stubble, calm fearless expression, "
        "subtle serene smirk, mouth firmly closed, wearing dark graphite tactical overshirt, "
        "matte steel compass pendant visible on neck, 35mm film photography, natural skin pores, "
        "authentic cinematic studio lighting, clean solid grey background, 8k resolution"
    )
    
    print("Generating character reference front portrait...")
    img = await api.generate_single_image(prompt=prompt, size="1024x1024")
    await img.save(str(out_file))
    print(f"Saved: {out_file.resolve()} (size: {out_file.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
