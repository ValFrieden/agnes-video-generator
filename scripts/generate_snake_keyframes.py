import asyncio
import os
import sys
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

BRAIN_DIR = "C:/Users/Valeri/.gemini/antigravity/brain/5206faf6-a4af-482f-ad2b-3902d5efa61a"

async def gen():
    api = AgnesImageAPI(api_key=get_api_key())
    prompt = (
        "35mm film photography, Kodak Vision3 500T, authentic cinematography. "
        "Camera strictly from behind (back-to-camera tracking shot). "
        "A rugged 34-year-old Caucasian man with short brown textured hair, wearing a dark graphite tactical jacket and dark cargo pants, "
        "walking forward with calm fearless posture into a deep red sandstone desert canyon. "
        "The rocky ground and gravel are naturally scattered with various wild desert snakes (rattlesnakes, vipers, and a desert cobra) "
        "crawling organically in completely asymmetrical positions: one rattlesnake crossing dry gravel on the right foreground, "
        "another viper coiled in deep rock shadow on the left, one cobra flaring its hood several meters ahead in distance. "
        "Completely non-mirrored, irregular organic spacing, authentic reptile biology with dry matte keeled scales, no rubber gloss. "
        "Harsh warm late afternoon sunlight, long dramatic shadows from canyon walls, airborne dust motes, ARRI Alexa optical texture, anti-slop, photorealistic."
    )
    print("Generating candidate keyframe 1...")
    out1 = await api.generate_single_image(prompt=prompt, size="1280x720")
    out_path1 = os.path.join(BRAIN_DIR, "snake_valley_cand1.jpg")
    await out1.save(out_path1)
    print("Saved 1 to:", out_path1)

    # Let's also do a low-angle variation focusing on the path and boots stepping calmly among rocks
    prompt2 = (
        "35mm cinematic film still, documentary photography, Kodak Vision3 500T. "
        "Camera low angle strictly from behind (back-to-camera tracking shot). "
        "A 34-year-old Caucasian man with short brown textured hair, wearing a dark graphite tactical overshirt, dark cargo pants, and distressed leather boots. "
        "He steps forward calmly and steadily on the sun-baked stony canyon floor, completely ignoring dozens of wild desert snakes. "
        "Rattlesnakes and desert vipers slither organically across dry red sand and between weathered sandstone boulders. "
        "Strict organic asymmetry: completely irregular placement, different depths, non-parallel angles of movement, realistic dry keeled reptilian scales. "
        "Golden hour rim light slicing through narrow canyon walls, fine dust motes, authentic wildlife cinematography, zero CGI gloss, zero mirror symmetry."
    )
    print("Generating candidate keyframe 2...")
    out2 = await api.generate_single_image(prompt=prompt2, size="1280x720")
    out_path2 = os.path.join(BRAIN_DIR, "snake_valley_cand2.jpg")
    await out2.save(out_path2)
    print("Saved 2 to:", out_path2)

if __name__ == "__main__":
    asyncio.run(gen())
