"""
generate_reference_bibles.py — Генерация канонических карт персонажей, дома, природы и предметов
для клипа «Дверь в другую вселенную».
"""
import asyncio
import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.api.key_manager import get_key_ring
from core.api.agnes_image import AgnesImageAPI

SHEETS = [
    {
        "filename": "door_frames/character_sheet_man.jpg",
        "prompt": (
            "Character model sheet, turnaround reference sheet of one handsome caucasian male character at two ages. "
            "On the left: 25 years old in 1930s linen shirt and trousers, wavy brown hair, kind hazel eyes, gentle jawline, front view, 3/4 view, and full body. "
            "On the right: the exact same man at 68 years old, neat silver hair, kind laugh lines, same bone structure and nose, wearing oatmeal knit cardigan, simple gold wedding band, front view, profile view, and full body. "
            "Consistent height, clean white studio background, neutral lighting, 35mm film photography style, award-winning cinematic character bible, ultra detailed."
        ),
        "ref": "door_frames/scene_02_newlyweds.jpg",
    },
    {
        "filename": "door_frames/character_sheet_woman.jpg",
        "prompt": (
            "Character model sheet, turnaround reference sheet of one beautiful gentle caucasian female character at two ages. "
            "On the left: 23 years old in 1930s white cotton lace dress, wavy blonde hair, radiant kind smile, delicate features, front view, 3/4 view, and full body. "
            "On the right: the exact same woman at 65 years old, soft silver-streaked hair softly pinned up, wearing a lavender knit shawl over cream dress, matching gold wedding band, front view, profile view, and full body. "
            "Consistent height (slightly shorter than husband), clean neutral background, 35mm film photography style, cinematic character bible, ultra detailed."
        ),
        "ref": "door_frames/scene_02_newlyweds.jpg",
    },
    {
        "filename": "door_frames/location_environment_sheet.jpg",
        "prompt": (
            "Environment concept art sheet, location reference board of one consistent countryside landscape: "
            "gentle rolling emerald green hills under a soft pastoral sky, one single old gnarly apple tree to the left of a rustic dirt path, "
            "wildflowers (purple lupines and daisies) growing naturally along the path. No steep mountains, no canyons, no cliffs, "
            "only smooth rolling hills and meadow shown from 4 different camera angles: wide establishing shot, medium meadow view, golden hour lighting, and twilight starry sky. "
            "Consistent topography, Kodak Vision3 35mm film still, master landscape cinematography."
        ),
        "ref": "door_frames/scene_01_intro.jpg",
    },
    {
        "filename": "door_frames/house_architecture_sheet.jpg",
        "prompt": (
            "Architecture and house model sheet, multi-angle reference sheet of one specific vintage wooden family house: "
            "Panel 1: Front exterior view showing the covered wooden porch with carved railings, stone foundation steps, and rustic oak entrance door. "
            "Panel 2: Side exterior view showing the apple tree and meadow path leading to the porch. "
            "Panel 3: Interior entryway showing the dark rustic oak front door from inside, wooden plank floor, and vertical oak doorframe with carved child height markings. "
            "Panel 4: Cozy corner with window overlooking the porch and rocking chair. "
            "Consistent architecture, weathered wood textures, 35mm film still, architectural bible."
        ),
        "ref": "door_frames/door_master_anchor.jpg",
    },
    {
        "filename": "door_frames/props_sheet.jpg",
        "prompt": (
            "Props and material reference sheet, still life photography board of key story objects: "
            "Item 1: Antique ornate brass key on a worn brown leather neck cord. "
            "Item 2: Extreme close-up of textured oak doorframe with hand-carved height measurement notches and vintage pencil dates. "
            "Item 3: Cozy chunky knit oatmeal cardigan wool texture and simple gold wedding band. "
            "Item 4: Soft knitted lavender wool shawl texture. "
            "Item 5: Two vintage porcelain tea cups on a weathered wooden table with red apples. "
            "Tactile macro photography, warm cinematic lighting, Kodak Vision3 500T, authentic textures."
        ),
        "ref": "door_frames/scene_07_touching_notches.jpg",
    },
]

async def main():
    key = get_key_ring().next()
    print("Using Agnes Image API with key:", key[:8] + "...")
    api = AgnesImageAPI(api_key=key)

    for item in SHEETS:
        out_path = item["filename"]
        print(f"\n--- Generating: {out_path} ---")
        refs = [item["ref"]] if os.path.exists(item["ref"]) else []
        try:
            res = await api.generate_single_image(
                prompt=item["prompt"],
                reference_image_paths=refs,
                size="1280x720",
                max_retries=3,
            )
            await res.save(out_path)
            print(f"SUCCESS: Saved {out_path}")
        except Exception as e:
            print(f"ERROR generating {out_path}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
