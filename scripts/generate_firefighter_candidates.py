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

    # Candidate 1: Tan Nomex turnout gear, low-angle tracking shot from behind, industrial structure fire
    prompt_cand1 = (
        "Cinematic 35mm film still, Kodak Vision3 500T, shot strictly from behind, low-angle rear tracking view. "
        "A professional firefighter in authentic tan heavy Nomex bunker gear, reflective lime-yellow and silver safety stripes, "
        "SCBA oxygen cylinder tank mounted on harness with pressure gauge on the back, structural firefighter helmet with extended rear brim. "
        "The firefighter holds a heavy fire axe at their side and walks calmly and fearlessly forward through a shattered doorway into a heavily burning industrial building. "
        "Inside, violent turbulent orange and yellow flames lick across the ceiling beams (rollover fire dynamics), thick rolling black and dark-charcoal smoke billowing beneath the roof. "
        "Swirling glowing embers and golden sparks floating through the air, heat distortion waves shimmer above the blaze. "
        "Wet concrete floor reflecting the roaring inferno, strictly back-to-camera, no human face shown. "
        "Authentic National Geographic / action cinematography, ARRI Alexa natural rendering, zero plastic 3D cgi, 16:9 widescreen"
    )

    # Candidate 2: Dark graphite turnout gear, medium over-the-shoulder shot from behind, blazing residential doorway
    prompt_cand2 = (
        "Cinematic medium over-the-shoulder shot strictly from behind, 35mm Master Prime lens f/2.0. "
        "A fearless firefighter wearing dark graphite heavy turnout coat with fluorescent neon-yellow reflective tape, "
        "breathing apparatus oxygen tank on the back, heavy fire gloves, black structural helmet seen from behind. "
        "The firefighter steps decisively across a burning threshold into an engulfed residential building interior ablaze with intense roaring flames. "
        "Burning wooden rafters and doorframe glowing with intense heat, turbulent convection currents carrying clouds of luminous golden sparks and deep grey pyrolytic smoke. "
        "Dramatic chiaroscuro lighting illuminated entirely by the fierce fire, silhouette rim lighting along the firefighter shoulders and tank. "
        "Strictly back to camera, zero facial features visible. Authentic physical fire behavior, natural smoke fluid dynamics, anti-slop, 16:9 widescreen"
    )

    print("Generating Candidate 1...", flush=True)
    out1 = await api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    p1 = os.path.join(out_dir, "firefighter_cand1_1280x720.png")
    await out1.save(p1)
    shutil.copyfile(p1, os.path.join(art_dir, "firefighter_cand1_1280x720.png"))
    print("Saved Cand 1 successfully:", p1, flush=True)

    print("Generating Candidate 2...", flush=True)
    out2 = await api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    p2 = os.path.join(out_dir, "firefighter_cand2_1280x720.png")
    await out2.save(p2)
    shutil.copyfile(p2, os.path.join(art_dir, "firefighter_cand2_1280x720.png"))
    print("Saved Cand 2 successfully:", p2, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
