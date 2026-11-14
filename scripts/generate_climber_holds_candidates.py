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

    # Candidate 1: Clear vertical splitter crack & finger fissures with white chalk marks, authentic rock climbing anatomy
    prompt_cand1 = (
        "Cinematic 35mm film photograph, Kodak Vision3 500T, authentic big wall free solo climbing, shot from behind. "
        "An athletic solo rock climber clings directly to a sheer vertical granite cliff high above the earth. "
        "Seen strictly from behind (Back-to-Camera, absolutely NO face visible), athletic back, chalk bag at waist. "
        "The rock wall has a prominent, deep natural vertical rock crack (splitter fissure) and distinct rock ledges and finger pockets running up the granite face. "
        "His hands and chalk-dusted fingers are firmly jammed and gripping inside the natural stone fissure and visible rocky handholds. "
        "His specialized climbing shoes are wedged on distinct small granite footholds and rock edges. "
        "White climbing chalk dust marks are clearly visible along the edges of the rock crack. "
        "To the left, the cliff drops into a terrifying 3,000-foot abyss down to a distant misty pine valley floor. "
        "Low warm morning sunlight raking across the textured stone, highlighting every fissure, crevice, and edge. "
        "Realistic climbing physics, National Geographic documentary authenticity, zero plastic CGI, 16:9 widescreen"
    )

    # Candidate 2: Textured cliff face with rugged crevices, finger pockets, natural granite flakes, and footholds
    prompt_cand2 = (
        "Master Prime 35mm lens, wide cinematic shot from behind, realistic extreme climbing photograph. "
        "A fearless free solo climber ascending a massive vertical granite wall over a colossal abyss. "
        "Strictly Back-to-Camera, 100% no visible face, wearing climbing shorts, chalk bag clipped to harness. "
        "The rock face is rich with natural climbing features: distinct horizontal and vertical crevices, sharp granite flakes, "
        "deep finger pockets, and natural stone notches that clearly provide real, believable holds for his hands and feet. "
        "White chalk marks coat the main handholds where his fingers grip the rock securely. "
        "Beneath him is an immense dizzying void of empty air, dropping thousands of feet into a vast sunlit mountain canyon below. "
        "Tactile rough granite texture, natural mineral striations, photorealistic physical climbing anatomy, anti-slop, 16:9 widescreen"
    )

    print("Generating Updated Candidate 1 (Distinct vertical crack & finger fissures)...", flush=True)
    out1 = await api.generate_single_image(prompt=prompt_cand1, size="1280x720")
    p1 = os.path.join(out_dir, "climber_holds_cand1_1280x720.png")
    await out1.save(p1)
    shutil.copyfile(p1, os.path.join(art_dir, "climber_holds_cand1_1280x720.png"))
    print("Saved Holds Cand 1 successfully:", p1, flush=True)

    print("Generating Updated Candidate 2 (Rugged crevices, pockets & stone flakes)...", flush=True)
    out2 = await api.generate_single_image(prompt=prompt_cand2, size="1280x720")
    p2 = os.path.join(out_dir, "climber_holds_cand2_1280x720.png")
    await out2.save(p2)
    shutil.copyfile(p2, os.path.join(art_dir, "climber_holds_cand2_1280x720.png"))
    print("Saved Holds Cand 2 successfully:", p2, flush=True)

    print("ALL UPDATED HOLDS CANDIDATES GENERATED!")

if __name__ == "__main__":
    asyncio.run(main())
