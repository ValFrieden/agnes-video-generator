import asyncio
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

async def main():
    api = AgnesImageAPI(api_key=get_api_key())
    art_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
    out_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames"

    # Candidate 1: Golden-hour big wall climber on colossal flat granite monolith, dramatic vertical abyss below
    prompt_cand1 = (
        "Cinematic 35mm film still, Kodak Vision3 500T, authentic big wall climbing photograph, shot from behind. "
        "An athletic solo rock climber clings directly to the sheer, immense flat vertical granite face of a colossal monolith cliff like El Capitan. "
        "Strictly seen from behind (Back-to-Camera, absolutely NO face visible), showing back, muscular shoulders, chalk dust bag on waist belt, "
        "fingers gripping a razor-thin granite crimp hold, specialized climbing shoes edging on micro-crystals. "
        "The colossal flat golden-grey granite wall rises endlessly, and directly beneath his feet is a terrifying dizzying abyss "
        "dropping three thousand feet into a distant misty valley floor with tiny pine trees. "
        "Warm low-angled morning sunlight rakes across the sheer rock face, revealing fine stone texture and chalk marks. "
        "Immense sense of vertical scale and exposure. ARRI Alexa cinematic quality, zero plastic 3D cgi, anti-slop, 16:9 widescreen"
    )

    # Candidate 2: High alpine vertical wall, cool airy atmosphere, climber like an ant on an infinite stone shield
    prompt_cand2 = (
        "Master Prime 32mm lens, wide cinematic shot from behind, National Geographic documentary realism. "
        "A fearless solo climber clinging to an enormous, smooth, flat vertical granite slab high in the mountains. "
        "Viewed strictly from behind (Back-to-Camera, 100% no visible face), wearing dark climbing gear, chalk bag, climbing shoes on tiny granite friction sloper. "
        "The camera frames him suspended in the center of an astronomical, flat, vertical stone wall that stretches far in all directions. "
        "Far below his boots, the cliff plunges vertically into a vast yawning canyon abyss filled with drifting white cloud layers and mountain mist. "
        "Crisp high-altitude alpine air, cool natural daylight, photorealistic granite grain, vertigo-inducing spatial depth, "
        "authentic human scaling against titanic nature, zero plastic 3D cgi, 16:9 widescreen"
    )

    print("Generating Candidate 1 (Golden hour flat granite monolith & climber)...", flush=True)
    out1 = await api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    p1 = os.path.join(out_dir, "climber_cand1_1280x720.png")
    await out1.save(p1)
    shutil.copyfile(p1, os.path.join(art_dir, "climber_cand1_1280x720.png"))
    print("Saved Cand 1 successfully:", p1, flush=True)

    print("Generating Candidate 2 (Alpine flat slab & misty abyss scale)...", flush=True)
    out2 = await api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    p2 = os.path.join(out_dir, "climber_cand2_1280x720.png")
    await out2.save(p2)
    shutil.copyfile(p2, os.path.join(art_dir, "climber_cand2_1280x720.png"))
    print("Saved Cand 2 successfully:", p2, flush=True)

    print("ALL CLIMBER CANDIDATES GENERATED!")

if __name__ == "__main__":
    asyncio.run(main())
