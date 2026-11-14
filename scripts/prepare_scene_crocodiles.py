import os
import sys
import json
import asyncio
import urllib.request
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.config import get_api_key
from core.api.agnes_image import AgnesImageAPI

REF_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\references_crocodiles"
os.makedirs(REF_DIR, exist_ok=True)
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

async def main():
    api_key = get_api_key()
    img_api = AgnesImageAPI(api_key=api_key)

    # 1. Candidate Keyframe 1: Muddy riverbank with basking Nile crocodiles, Back-to-Camera
    prompt_cand1 = (
        "Cinematic 35mm film still, Kodak Vision3 500T texture, ARRI Alexa optical rendering. "
        "A solitary 34-year-old athletic Caucasian man seen strictly from behind (Back-to-Camera, absolutely NO visible face, "
        "dark graphite tactical overshirt, dark cargo pants, distressed muddy leather boots, brown textured hair) walks calmly "
        "and fearlessly forward along the muddy shoreline of a wide murky tropical river. "
        "ANATOMICAL CROCODILE REALISM: Massive wild Nile crocodiles (4 to 5 meters long) rest naturally on the wet river silt "
        "and sandbanks. Heavy armored osteoderms, dark olive-brown keeled dorsal scutes encrusted with dried river mud. "
        "Some crocodiles bask with heavy jaws slightly ajar in natural behavioral thermoregulation, while others lie motionless "
        "half-submerged with only their elevated nostrils, textured brow ridges, and ridged tails visible in the dark brown water. "
        "STRICT ORGANIC ASYMMETRY: Reptiles are irregularly scattered at different depths, angles, and distances from the man, "
        "completely non-mirrored, organic biological distribution. Low-angle tracking shot from behind at waist height. "
        "Atmospheric humid tropical mist, warm early morning haze filtering through rainforest trees in distance. "
        "Anti-slop, realistic animal scale, zero plastic CGI gloss, authentic documentary cinematography."
    )

    # 2. Candidate Keyframe 2: Wider tracking shot, wet mud flats, crocodiles slowly crawling/sliding into water
    prompt_cand2 = (
        "Cinematic 35mm photography, master shot. "
        "A rugged man seen strictly from behind (Back-to-Camera, dark tactical overshirt, graphite cargo trousers, distressed boots, "
        "short brown hair, NO visible face) walks steadily forward across an expansive muddy riverbank at dawn. "
        "Dozens of giant saltwater crocodiles rest and slowly crawl along the mud flats toward the murky river. "
        "REALISTIC BIOMECHANICS & TEXTURE: Densely armored dermal scutes, wet muddy sheen, low heavy bellies resting directly on "
        "wet silt, muscular clawed limbs planted naturally. Two crocodiles slowly slide belly-first down the wet mud into the dark river ripples. "
        "Organic asymmetric placement: varied reptile sizes, non-parallel positions, random natural cluster. "
        "Golden morning sunlight slicing through jungle vapor, creating soft silhouettes and specular highlights on wet crocodile hides. "
        "Documentary realism, ARRI Alexa LF, 35mm prime lens, ultra-detailed skin textures, anti-slop, photorealistic."
    )

    print("Generating Candidate Keyframe 1 (1280x720)...", flush=True)
    cand1_path = os.path.join(REF_DIR, "crocodiles_option1_1280x720.png")
    out1 = await img_api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    await out1.save(cand1_path)
    shutil.copy2(cand1_path, os.path.join(ARTIFACT_DIR, "crocodiles_option1_1280x720.png"))
    print("Candidate 1 saved!", flush=True)

    print("\nGenerating Candidate Keyframe 2 (1280x720)...", flush=True)
    cand2_path = os.path.join(REF_DIR, "crocodiles_option2_1280x720.png")
    out2 = await img_api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    await out2.save(cand2_path)
    shutil.copy2(cand2_path, os.path.join(ARTIFACT_DIR, "crocodiles_option2_1280x720.png"))
    print("Candidate 2 saved!", flush=True)

    print("\nAll candidate keyframes generated successfully!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
