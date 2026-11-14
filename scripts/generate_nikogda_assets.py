#!/usr/bin/env python3
"""scripts/generate_nikogda_assets.py — Генератор референсов персонажа и ключевых кадров сцен для клипа «Никогда не боюсь».

Создаёт:
1. Эталонные ракурсы персонажа Valeri (Front, 3/4, Profile, Back, Fullbody).
2. Контактный лист персонажа (character_sheet.png).
3. 18 ключевых кадров сцен 16:9 (1344x768) для Image-to-Video в Google Flow.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("NikogdaAssets")

OUT_DIR = Path("nikogda_ne_boyus_frames")

CHARACTER_PROMPTS = {
    "character_front.png": (
        "Character design reference portrait, front view close-up of 34-year-old rugged Caucasian man Valeri, "
        "short matte brown textured hair, piercing grey-green eyes, well-groomed light stubble, calm fearless expression, "
        "subtle serene smirk, mouth firmly closed, wearing dark graphite tactical overshirt, "
        "matte steel compass pendant visible on neck, 35mm film photography, natural skin pores, "
        "authentic cinematic studio lighting, clean solid grey background, 8k resolution"
    ),
    "character_34.png": (
        "Character design reference, three-quarter angle portrait, 34-year-old rugged Caucasian man Valeri, "
        "short matte brown hair, grey-green eyes, light stubble, resolute jawline, mouth closed with tranquil confidence, "
        "dark graphite tactical overshirt, soft golden rim lighting on cheek, authentic photorealistic 35mm portrait, "
        "neutral studio backdrop"
    ),
    "character_profile.png": (
        "Character design reference, side profile portrait, 34-year-old rugged Caucasian man Valeri, "
        "short matte brown hair, straight nose, defined jawline with neat stubble, looking calmly toward horizon, "
        "dark graphite tactical overshirt collar, dramatic chiaroscuro side lighting, cinematic realism, clean background"
    ),
    "character_back.png": (
        "Character design reference, full back view, 34-year-old athletic man seen from behind, "
        "short matte brown hair at nape, broad shoulders in dark graphite tactical overshirt, dark cargo pants, "
        "distressed leather boots, standing relaxed and upright against neutral studio background"
    ),
    "character_fullbody.png": (
        "Character design reference turnaround sheet, full body shot of 34-year-old athletic Caucasian man Valeri "
        "standing in confident neutral posture, short matte brown hair, grey-green eyes, light stubble, "
        "wearing dark graphite tactical overshirt, dark cargo pants, distressed leather boots, hands relaxed at sides, "
        "matte steel compass pendant around neck, 35mm lens full figure shot, clean background"
    ),
}

SCENE_PROMPTS = {
    "scene_01.png": (
        "Cinematic wide establishing shot, open cargo ramp of a military transport plane flying above stormy thunderclouds at 10,000 feet. "
        "34-year-old rugged Caucasian man Valeri, athletic build, short matte brown hair, grey-green eyes, light stubble, "
        "dark graphite tactical overshirt billowing in cold high-altitude wind, distressed leather boots, steel compass pendant on neck, "
        "standing calmly on the very edge of the abyss with a peaceful confident smile, about to step backward into the clouds, "
        "cold indigo lighting, lightning flashes, 35mm film grain, 16:9 widescreen"
    ),
    "scene_02.png": (
        "Cinematic aerial skydiving wide shot at sunset, high above dramatic cloud valleys. "
        "34-year-old Caucasian man Valeri in freefall belly-to-earth posture, short brown hair, grey-green eyes, light stubble, "
        "wearing dark graphite tactical overshirt, bare hands giving a casual thumbs-up 'class' gesture toward camera, "
        "warm golden sunset rim light illuminating the horizon, joyful serene fearless expression, photorealistic live-action, 16:9"
    ),
    "scene_03.png": (
        "Low-angle cinematic tracking shot in a red rock desert canyon. Ground carpeted with hundreds of crawling rattlesnakes, "
        "vipers, and cobras flaring hoods. 34-year-old rugged Caucasian man Valeri, short matte brown hair, grey-green eyes, "
        "light stubble, dark graphite tactical overshirt, dark cargo pants, distressed leather boots cleanly stepping between serpents, "
        "unbothered upright posture, calm subtle smile, looking straight ahead, harsh cinematic desert sunlight, 16:9"
    ),
    "scene_04.png": (
        "Cinematic medium tracking shot along a muddy tropical riverbank. Dozens of massive wild crocodiles basking with jaws agape on sand. "
        "34-year-old rugged Caucasian man Valeri strolling calmly along the water's edge in leather boots, casually brushing his hand "
        "over the armored scales of a resting crocodile, dark graphite tactical overshirt, steel compass pendant, tranquil amused smirk, "
        "atmospheric humid jungle lighting, 35mm film, 16:9"
    ),
    "scene_05.png": (
        "Medium shot in deep primeval rainforest, golden sun rays cutting through dense foliage. "
        "A huge buzzing swarm of thousands of giant wild bees and hornets swirls in the air. "
        "34-year-old rugged Caucasian man Valeri walking smoothly through the swarm with closed eyes, breathing deeply, "
        "dark graphite tactical overshirt, peaceful meditative aura, insects flying inches from his stubble, cinematic chiaroscuro, 16:9"
    ),
    "scene_06.png": (
        "Monumental low-angle hero shot on the razor edge of an erupting volcano crater at night. "
        "Columns of molten orange lava shooting into dark sky in background, glowing sparks drifting. "
        "34-year-old rugged Caucasian man Valeri standing solid as a granite rock, dark graphite tactical overshirt, steel compass pendant, "
        "resolute fearless gaze facing the fiery abyss, warm rim light from magma, IMAX cinematography, 16:9"
    ),
    "scene_07.png": (
        "Cinematic wide shot in vast prairie plains facing a colossal F5 tornado twisting across the landscape. "
        "Violent hurricane winds, dust clouds, bent trees. 34-year-old rugged Caucasian man Valeri walking forward directly into the gale, "
        "dark graphite tactical overshirt whipping in wind, steady grounded stride, fearless ecstatic grin facing the storm, 16:9"
    ),
    "scene_08.png": (
        "Action follow shot of high-speed proximity wingsuit flying inside a narrow granite canyon gorge at 200 km/h. "
        "34-year-old Caucasian man Valeri in sleek graphite aerodynamic wingsuit, bare face exposed with short brown hair, "
        "grey-green eyes, light stubble, carving around sharp rock spires with extreme skill and sheer adrenaline joy, 16:9"
    ),
    "scene_09.png": (
        "Cinematic slow-motion 120fps medium shot on an industrial suspension bridge. "
        "A massive fiery orange explosion detonates behind him, throwing steel beams and sparks into the air. "
        "34-year-old rugged Caucasian man Valeri walking calmly toward camera without turning around, "
        "dark graphite tactical overshirt, steel compass pendant, tranquil stoic expression, warm explosion rim light, 16:9"
    ),
    "scene_10.png": (
        "Hero close-up portrait against a towering wall of blazing fire and starry midnight sky. "
        "34-year-old rugged Caucasian man Valeri, short matte brown hair, piercing grey-green eyes reflecting sparks, "
        "light stubble, broad triumphant infectious smile of total invincibility, chest breathing deeply, cinematic Kodak 500T, 16:9"
    ),
    "scene_11.png": (
        "Cinematic action tracking shot down a foggy ruined post-apocalyptic city street filled with smoking car wrecks and a terrifying horde of pale zombies reaching out. "
        "In the background, panicked civilians are fleeing in terror. In the foreground, 34-year-old rugged Caucasian man Valeri is casually jogging through the zombie horde "
        "like on a morning run with discreet earbuds, short brown hair, grey-green eyes, light stubble, dark graphite tactical overshirt, athletic effortless agility, "
        "weaving past grabbing zombie arms with a playful relaxed smile, giving a two-finger peace sign ✌️ to the camera, 35mm film, 16:9 widescreen"
    ),
    "scene_12.png": (
        "Ground-level cinematic tracking shot on wet neon city street. The panicked crowd rushes past in heavy motion blur. "
        "In the center, 34-year-old rugged Caucasian man Valeri walks steadily in the opposite direction against the flow of people. "
        "Wet short brown hair, grey-green eyes, light stubble, wet dark graphite tactical overshirt, relaxed stride, serene fearless smile, 16:9"
    ),
    "scene_13.png": (
        "Low-angle medium shot on rain-slicked city pavement. A terrified young civilian slips and falls on the wet ground. "
        "34-year-old rugged Caucasian man Valeri extends a strong hand, lifting him effortlessly to his feet with an encouraging, "
        "warm brotherly smile, wet dark graphite overshirt, steel compass pendant, warm amber neon light from a café window, 16:9"
    ),
    "scene_14.png": (
        "Epic wide low-angle hero shot in a city square under storm clouds. "
        "34-year-old rugged Caucasian man Valeri standing in the center, triumphantly raising both fists and arms high into the air. "
        "Fleeing citizens have stopped in their tracks, turning around inspired, raising their hands together in defiance and solidarity, 16:9"
    ),
    "scene_15.png": (
        "Majestic panoramic action shot across golden desert dunes during a towering 100-meter sandstorm wall at sunset. "
        "34-year-old rugged Caucasian man Valeri riding bareback at full gallop on a muscular black stallion along the ridge of the dune, "
        "dark graphite tactical overshirt, steel compass pendant, joyful fearless freedom, golden hour lighting, 16:9"
    ),
    "scene_16.png": (
        "Extreme low-angle hero shot on the bow of an ocean trawler battling 15-meter freezing turquoise waves in the North Atlantic. "
        "A colossal sea wave crashes over the deck, white sea foam exploding. 34-year-old rugged Caucasian man Valeri holding the steel railing "
        "with one hand, water pouring down his laughing face, shouting defiantly into the storm, pure unstoppable vitality, 16:9"
    ),
    "scene_17.png": (
        "Breathtaking high-angle shot from the summit of an alpine mountain peak bathed in golden sunrise above an ocean of clouds. "
        "34-year-old rugged Caucasian man Valeri standing on the sharp stone peak, dark graphite tactical overshirt, "
        "taking a deep victorious breath overlooking the infinite morning horizon, pure serenity and triumph, 16:9"
    ),
    "scene_18.png": (
        "Cinematic wide landscape shot of an endless asphalt highway cutting through golden sunrise plains. "
        "34-year-old rugged Caucasian man Valeri pauses on the road, turns toward camera, dusting off his shoulder with a quiet confident breath, "
        "giving a warm, knowing wink and smile straight into the lens, before walking peacefully toward the rising sun, 16:9"
    ),
}

async def generate_images(prompts_dict, size="1344x768"):
    api_key = get_api_key()
    api = AgnesImageAPI(api_key=api_key)
    OUT_DIR.mkdir(exist_ok=True)
    
    for filename, prompt in prompts_dict.items():
        target_path = OUT_DIR / filename
        if target_path.exists() and target_path.stat().st_size > 1000:
            logger.info(f"Skipping existing: {filename}")
            continue
            
        logger.info(f"Generating {filename} ({size})...")
        try:
            img = await api.generate_single_image(prompt=prompt, size=size)
            await img.save(str(target_path))
            logger.info(f"Successfully saved {filename} ({target_path.stat().st_size} bytes)")
        except Exception as e:
            logger.error(f"Failed to generate {filename}: {e}")
        await asyncio.sleep(2)

def build_character_sheet():
    parts = ["character_front.png", "character_34.png", "character_profile.png", "character_back.png"]
    images = []
    for p in parts:
        f = OUT_DIR / p
        if f.exists():
            images.append(Image.open(f))
            
    if len(images) == 4:
        w, h = images[0].size
        sheet = Image.new("RGB", (w * 4, h))
        for idx, im in enumerate(images):
            sheet.paste(im, (idx * w, 0))
        sheet_path = OUT_DIR / "character_sheet.png"
        sheet.save(sheet_path)
        logger.info(f"Character sheet saved to {sheet_path}")

async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("char", "all"):
        logger.info("=== GENERATING CHARACTER REFS ===")
        await generate_images(CHARACTER_PROMPTS, size="1024x1024")
        build_character_sheet()
        
    if mode in ("scenes", "all"):
        logger.info("=== GENERATING SCENE KEYFRAMES ===")
        await generate_images(SCENE_PROMPTS, size="1344x768")

if __name__ == "__main__":
    asyncio.run(main())
