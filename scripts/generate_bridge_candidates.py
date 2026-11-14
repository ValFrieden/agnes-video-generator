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

    # Candidate 1: Karakoram / Himalayan alpine cliff, dramatic perspective looking down across the abyss
    prompt_cand1 = (
        "Cinematic 35mm film still, Kodak Vision3 500T, dramatic wide shot from behind. "
        "A lone courageous traveler in a rugged canvas mountain field jacket, cargo trousers, and worn hiking boots "
        "stands at the sheer rocky edge of a massive mountain cliff, stepping forward onto the first weathered wooden planks "
        "of a perilous rope suspension bridge that hangs across a bottomless, dizzying abyss. "
        "The narrow rustic bridge consists of weathered timber slats tied to thick steel cables, with visible scary gaps between planks "
        "revealing the terrifying drop hundreds of meters down into a misty mountain gorge. "
        "The bridge sways slightly in the high-altitude alpine wind. "
        "Epic Karakoram mountain peaks and dramatic clouds in the background. "
        "Strictly back to camera, absolutely NO face visible. "
        "ARRI Alexa natural cinematic lighting, authentic mountain texture, real rope and wood physics, zero plastic 3D cgi, 16:9 widescreen"
    )

    # Candidate 2: Over-the-shoulder vertigo perspective into a cloud-shrouded canyon abyss
    prompt_cand2 = (
        "Cinematic wide angle over-the-shoulder shot, Master Prime 28mm lens f/2.8. "
        "A solitary fearless explorer in a dark hooded windbreaker jacket stands right at the precipice of a vertical granite precipice, "
        "fearlessly walking forward onto an ancient, swaying suspension bridge that spans across a colossal yawning chasm. "
        "Directly beneath the bridge is an immense, terrifying void with sheer vertical rock walls dropping thousands of feet into swirling white clouds and fog below. "
        "Sunbeams break through high mountain mist, illuminating the weathered wooden planks and rusted tension cables. "
        "Intense sense of vertigo, scale, and danger. "
        "Strictly back to camera, zero facial features. "
        "Authentic documentary film aesthetic, National Geographic realism, anti-slop, 16:9 widescreen"
    )

    print("Generating Candidate 1 (Himalayan cliff & perilous suspension bridge)...", flush=True)
    out1 = await api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    p1 = os.path.join(out_dir, "bridge_cand1_1280x720.png")
    await out1.save(p1)
    shutil.copyfile(p1, os.path.join(art_dir, "bridge_cand1_1280x720.png"))
    print("Saved Cand 1 successfully:", p1, flush=True)

    print("Generating Candidate 2 (Vertigo cloud-canyon & swaying rope bridge)...", flush=True)
    out2 = await api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    p2 = os.path.join(out_dir, "bridge_cand2_1280x720.png")
    await out2.save(p2)
    shutil.copyfile(p2, os.path.join(art_dir, "bridge_cand2_1280x720.png"))
    print("Saved Cand 2 successfully:", p2, flush=True)

    print("ALL CANDIDATES GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
