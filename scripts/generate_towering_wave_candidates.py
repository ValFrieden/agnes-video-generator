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

    # Candidate 1: Low-angle shot looking up. A colossal 5-meter shorebreak wave curls directly overhead, pitching forward onto the rocky shore right in front of the fearless woman in emerald dress.
    prompt_cand1 = (
        "Cinematic 35mm film still, Kodak Vision3 500T, dramatic extreme low-angle shot from behind. "
        "A slender young woman in a fluttering emerald-green summer dress stands completely fearless and motionless "
        "on the wet dark shoreline rocks. "
        "Towering directly in front of her and curling overhead is a monstrous, colossal 5-meter wave. "
        "The massive, curved wall of dark emerald ocean water looms high above her, its heavy foamy crest pitching forward "
        "and crashing violently down onto the rocky ground right before her feet. "
        "Dramatic hollow tube barrel, explosive plumes of white sea spray, foam trails streaking down the concave face. "
        "The woman stands small against this titanic curtain of falling water, hair whipped by the gale. "
        "Strictly back to camera, no face visible. Intense cinematic lighting, ARRI Alexa natural documentary color, "
        "fluid dynamics of heavy crashing ocean water, zero plastic 3D cgi, 16:9 widescreen"
    )

    # Candidate 2: Over-the-shoulder shot of a massive catastrophic tidal wave wall curling and collapsing directly in front of a woman in a white linen dress.
    prompt_cand2 = (
        "Cinematic wide angle shot from behind, Master Prime 24mm lens f/2.8. "
        "A fragile yet calm woman in a light white summer dress stands barefoot at the water's edge on a glistening black rock ledge. "
        "Right before her, a titanic 5-meter wall of ocean water has reared up vertically and is violently folding over, "
        "its heavy curling lip about to smash down with thunderous impact onto the stone shore directly in front of her. "
        "Violent turbulence, tons of churning white foam and airborne spray swirling in the coastal gale. "
        "The towering wave dominates the entire upper frame, creating a terrifying sense of immense scale and imminent impact. "
        "Strictly back to camera, zero facial features. Cold stormy North Atlantic atmosphere, dramatic overcast sky, "
        "authentic natural water weight and physics, anti-slop, 16:9 widescreen"
    )

    print("Generating Candidate 1 (Towering 5m curling wave & emerald dress)...", flush=True)
    out1 = await api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    p1 = os.path.join(out_dir, "towering_wave_cand1_1280x720.png")
    await out1.save(p1)
    shutil.copyfile(p1, os.path.join(art_dir, "towering_wave_cand1_1280x720.png"))
    print("Saved Cand 1 successfully:", p1, flush=True)

    print("Generating Candidate 2 (Colossal wave collapsing onto shore & white dress)...", flush=True)
    out2 = await api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    p2 = os.path.join(out_dir, "towering_wave_cand2_1280x720.png")
    await out2.save(p2)
    shutil.copyfile(p2, os.path.join(art_dir, "towering_wave_cand2_1280x720.png"))
    print("Saved Cand 2 successfully:", p2, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
