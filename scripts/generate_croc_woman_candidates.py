import os
import sys
import asyncio
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

    # Prompt Candidate 1: Calm barefoot woman in light linen dress walking along muddy riverbank with real Nile crocodiles
    prompt_cand1 = (
        "National Geographic documentary cinematography, 35mm film still, ARRI Alexa LF natural color grading. "
        "A slender fearless young woman seen strictly from behind (Back-to-Camera, absolutely NO visible face, "
        "natural wavy brunette hair resting on her shoulders, wearing a simple understated earthy sand-colored linen summer dress, "
        "completely barefoot) walks calmly and serenely forward along the wet muddy shoreline of a vast African tropical river at early sunrise. "
        "HER BARE FEET leave authentic shallow impressions in the dark wet river silt and shallow water. "
        "BIOLOGICAL ANIMAL REALISM: Massive wild Nile crocodiles (4 to 5 meters) rest naturally scattered across the mudbank and in the shallow murky brown water. "
        "Their armored dorsal osteoderms are heavily encrusted with dried river mud and glistening with wet river sheen. "
        "Some crocodiles lie motionless with jaws slightly parted in natural basking thermoregulation, others rest heavy bellies directly in wet silt. "
        "ORGANIC ASYMMETRY: Non-mirrored, realistic irregular spacing across different depths and angles, natural river debris and scattered driftwood. "
        "Soft diffused morning river mist, golden sun rays cutting through tall acacia and riverine trees in distance. "
        "Zero plastic CGI gloss, realistic reptilian skin scale, authentic nature photography, anti-slop, true 35mm cinema texture."
    )

    # Prompt Candidate 2: Slightly wider environmental shot, shallow river margin, golden backlighting
    prompt_cand2 = (
        "Master wildlife documentary still, 35mm photography, Kodak Vision3 250D natural grain. "
        "A graceful fearless woman seen strictly from behind (Back-to-Camera, NO face shown, casual textured hair, "
        "wearing a lightweight olive-khaki cotton travel slip dress, barefoot) walks steadily along the wide muddy sandbar of a murky tropical river. "
        "Her bare feet step lightly through ankle-deep dark river water creating delicate ripples. "
        "WILDLIFE REALISM & NATURE DYNAMICS: Dozens of giant wild crocodiles bask lazily on the muddy riverbank. "
        "Two large crocodiles in mid-ground slowly crawl with low heavy bellies into the river current, displacing brown water with gentle concentric waves. "
        "Real weathered scutes, dark olive-brown river mud tones, completely organic non-uniform placement at varying distances. "
        "Atmospheric low-angle tracking shot from behind at waist height. Warm golden morning sunlight glancing across the water surface and wet mud flats. "
        "High-end BBC Earth aesthetic, anti-slop, true optical depth of field, authentic wild nature."
    )

    print("Generating Candidate 1: Woman barefoot with Nile crocodiles (1280x720)...", flush=True)
    c1_path = os.path.join(REF_DIR, "croc_woman_cand1_1280x720.png")
    out1 = await img_api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    await out1.save(c1_path)
    shutil.copy2(c1_path, os.path.join(ARTIFACT_DIR, "croc_woman_cand1_1280x720.png"))
    print("Candidate 1 saved!", flush=True)

    print("\nGenerating Candidate 2: Woman barefoot, wide environmental riverbank (1280x720)...", flush=True)
    c2_path = os.path.join(REF_DIR, "croc_woman_cand2_1280x720.png")
    out2 = await img_api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    await out2.save(c2_path)
    shutil.copy2(c2_path, os.path.join(ARTIFACT_DIR, "croc_woman_cand2_1280x720.png"))
    print("Candidate 2 saved!", flush=True)

    print("\nBoth candidates generated successfully!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
