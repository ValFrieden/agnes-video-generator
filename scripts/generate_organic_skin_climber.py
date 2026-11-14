import asyncio
import os
import sys
import shutil
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

def apply_subtle_film_emulation(img_path: str, out_path: str):
    """
    Applies analog 35mm film emulation:
    - Subtle organic monochromatic silver-halide grain (disrupts AI plastic smoothness & color banding)
    - Gentle film curve (lift shadows slightly to film pedestal, roll off harsh digital clip)
    - Natural micro-contrast enhancement without harsh edge halos
    """
    im = Image.open(img_path).convert('RGB')
    arr = np.array(im, dtype=np.float32)

    # 1. Subtle analog grain
    np.random.seed(42)
    grain = np.random.normal(loc=0.0, scale=3.5, size=(arr.shape[0], arr.shape[1], 1))
    arr = arr + grain
    arr = np.clip(arr, 0, 255)

    # 2. Organic film tonal response (subtle contrast & warm shadow lift)
    # Normalize 0..1
    norm = arr / 255.0
    # Soft S-curve
    curved = 0.5 * (1.0 - np.cos(np.pi * norm))
    # Blend 85% original, 15% film curve
    blended = norm * 0.85 + curved * 0.15
    result = np.clip(blended * 255.0, 0, 255).astype(np.uint8)

    res_im = Image.fromarray(result)
    res_im.save(out_path, quality=95)
    return out_path

async def main():
    api = AgnesImageAPI(api_key=get_api_key())
    art_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
    out_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames"

    # Option A: Authentic Documentary Free Soloist (Yosemite style granite splitter crack)
    prompt_organic_1 = (
        "Documentary 35mm photograph, National Geographic editorial style, shot on ARRI Alexa 35 with Cooke S4/i 35mm prime lens at f/2.8, unretouched raw candid photography. "
        "Strictly Back-to-Camera, 100% no visible face, athletic male rock climber ascending a sheer vertical granite wall high above the earth. "
        "Authentic human skin biology and optics: subsurface scattering (SSS) with warm reddish capillary undertones across back and shoulder muscles, "
        "visible dermal pores, natural skin micro-texture, fine vellus hair (peach fuzz) catching raking side-light, slight organic erythema and natural flushing from intense physical exertion, "
        "microscopic beads of natural perspiration with matte skin sheen (zero plastic gloss, zero oil sheen). "
        "Forearms and knuckles dusted with white gymnastic chalk powder. "
        "The climber grips firmly inside a deep, jagged vertical rock splitter crack in coarse quartz-monzonite granite. "
        "Climbing shoes firmly wedged into a sharp natural stone edge. "
        "Terrifying 3,000-foot vertical abyss dropping below into misty alpine canyon. "
        "Directional raking morning sunlight at 45 degrees revealing authentic rock crystals and true skin texture. "
        "Negative prompt: plastic, wax figure, mannequin, claymation, smooth airbrushed skin, cgi, 3d render, doll, video game character, porcelain skin, oversaturated orange tan, synthetic gloss, flat lighting"
    )

    # Option B: High-Alpine Big Wall Climber with authentic rock holds and gritty realism
    prompt_organic_2 = (
        "Editorial outdoor adventure photography, Kodak Portra 400 film stock, authentic tactile documentary realism. "
        "Viewed strictly from behind (Back-to-Camera, no face visible), lean rock climber with natural sun-exposed skin clinging to a vertical mountain monolith. "
        "Realistic skin anatomy: non-uniform natural Caucasian skin tone, visible micro-pores, fine dermal grain, natural vascularity on forearms, "
        "subsurface scattering giving warm blood-flow warmth to ear cartilage and shoulder edges under sunlight, "
        "dry powdery white climbing chalk smudged on hands, wrists, and rock edges. Absolutely no airbrushing or plastic smoothing. "
        "The granite cliff features authentic climbing holds: deep horizontal rock pockets, rugged natural crimps, and fractured fissures. "
        "Dizzying vertical drop beneath him revealing expansive atmospheric depth of an alpine valley far below. "
        "Natural directional alpine light, authentic optical depth of field, f/2.8 bokeh in distance, zero synthetic CGI"
    )

    print("Generating Organic Skin Candidate 1...", flush=True)
    out1 = await api.generate_single_image(prompt=prompt_organic_1, size="1280x720")
    raw1 = os.path.join(out_dir, "raw_climber_organic_cand1.png")
    await out1.save(raw1)
    
    p1 = os.path.join(out_dir, "climber_organic_cand1_1280x720.png")
    apply_subtle_film_emulation(raw1, p1)
    shutil.copyfile(p1, os.path.join(art_dir, "climber_organic_cand1_1280x720.png"))
    print("Saved Organic Cand 1:", p1, flush=True)

    print("Generating Organic Skin Candidate 2...", flush=True)
    out2 = await api.generate_single_image(prompt=prompt_organic_2, size="1280x720")
    raw2 = os.path.join(out_dir, "raw_climber_organic_cand2.png")
    await out2.save(raw2)

    p2 = os.path.join(out_dir, "climber_organic_cand2_1280x720.png")
    apply_subtle_film_emulation(raw2, p2)
    shutil.copyfile(p2, os.path.join(art_dir, "climber_organic_cand2_1280x720.png"))
    print("Saved Organic Cand 2:", p2, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
