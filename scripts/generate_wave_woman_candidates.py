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

    # Candidate 1: Emerald summer dress, high dark basalt cliff, colossal 15m Atlantic wave peaking
    prompt_cand1 = (
        "Cinematic 35mm film still, Kodak Vision3 500T, shot strictly from behind, low-angle rear view. "
        "A slender, fearless young woman wearing a light emerald-green summer dress stands completely calm and still "
        "on the edge of a wet, dark basalt rocky cliff facing the open ocean. "
        "The gale-force coastal wind aggressively whips the light fabric of her dress and her long brunette hair. "
        "Directly in front of her, a titanic 15-meter ocean swell rises into a monstrous cresting wave, "
        "with heavy dark-emerald water mass, deep textured ridges, and turbulent plumes of white sea spray blown backward by the storm wind. "
        "Wet glistening rock surface with reflections of the foaming surf, dramatic overcast storm sky. "
        "Strictly back to camera, no human face shown. National Geographic documentary realism, ARRI Alexa natural rendering, "
        "zero plastic 3D cgi, zero AI gloss, 16:9 widescreen"
    )

    # Candidate 2: White linen summer dress, wet granite sea shelf, massive wave crashing with explosive foam plume
    prompt_cand2 = (
        "Cinematic documentary photograph, over-the-shoulder wide shot strictly from behind, 35mm Master Prime lens f/2.4. "
        "A fragile yet fearless young woman in a flowing white linen sleeveless summer dress stands barefoot "
        "on a glistening wet granite rocky ledge overlooking a tempestuous North Atlantic ocean. "
        "The powerful sea wind billows the hem of her light dress towards the camera. "
        "A colossal ocean wave crashes with explosive, thunderous power against the jagged black reefs in front of her, "
        "launching an immense plume of violent white foam, churning sea froth, and airborne salt spray high into the cold grey air. "
        "Chilly deep-blue and charcoal sea tones, genuine fluid dynamics of heavy aerated water, "
        "strictly back-to-camera, no visible facial features. Anti-slop, authentic cinematic grain, 16:9 widescreen"
    )

    print("Generating Candidate 1 (Emerald dress & peaking wave)...", flush=True)
    out1 = await api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    p1 = os.path.join(out_dir, "wave_woman_cand1_1280x720.png")
    await out1.save(p1)
    shutil.copyfile(p1, os.path.join(art_dir, "wave_woman_cand1_1280x720.png"))
    print("Saved Cand 1 successfully:", p1, flush=True)

    print("Generating Candidate 2 (White linen dress & crashing wave)...", flush=True)
    out2 = await api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    p2 = os.path.join(out_dir, "wave_woman_cand2_1280x720.png")
    await out2.save(p2)
    shutil.copyfile(p2, os.path.join(art_dir, "wave_woman_cand2_1280x720.png"))
    print("Saved Cand 2 successfully:", p2, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
