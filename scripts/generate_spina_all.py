import asyncio
import os
import sys
from pathlib import Path

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.api.agnes_image import AgnesImageAPI
from core.config import get_api_key

OUT_DIR = ROOT / "kuda_idu_frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SPINA_SCENES = [
    {
        "id": "01",
        "title": "Вход в темноту",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a middle-aged man in a worn work canvas jacket, camera at shoulder height, standing before an immense pitch-black doorway threshold, stepping forward into complete darkness, single dim rim-light on his sturdy shoulders, resolute posture"
    },
    {
        "id": "02",
        "title": "Рассветный двор",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a woman in a long woolen dark coat walking away across a vast empty courtyard of old buildings, soft golden morning sunrise light falling tenderly across her shoulders, long gentle shadows stretching ahead"
    },
    {
        "id": "03",
        "title": "Дождь",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a young man in a thin jacket walking away down a glistening wet empty asphalt road under a dense curtain of pouring rain, rain streams glistening on the wet fabric of his back, solitary quiet persistence"
    },
    {
        "id": "04",
        "title": "Ветер",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of an elderly man in a heavy coat walking across an open windy autumn grassland, a long woolen scarf violently fluttering to the side, leaning forward into the powerful gale, unstoppable forward pace"
    },
    {
        "id": "05",
        "title": "Снег",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a young woman in a light winter jacket walking away across an untouched pristine white snowy plain, making the very first trail of footprints in the fresh snow under a soft overcast pearlescent sky, clean peaceful solitude"
    },
    {
        "id": "06",
        "title": "Метель",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a man in a dark hooded down jacket fighting his way forward into a howling white blizzard, tense broad back, swirling snow particles engulfing his silhouette, sheer stubborn willpower"
    },
    {
        "id": "07",
        "title": "Выход из метели",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a dark silhouette stepping out from a retreating wall of snowstorm into an expansive open valley flooded with glorious bright golden sunlight, shoulders relaxing, pure breath of liberation"
    },
    {
        "id": "08",
        "title": "Поле травы",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Low-angle tracking shot from behind of a 10-year-old child with a small canvas backpack running forward through waist-high green summer grass, arms outstretched sideways, golden late afternoon sun glowing through the wild blades, exhilarating joy of motion"
    },
    {
        "id": "09",
        "title": "Спина на фоне огня",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a man in a sturdy canvas jacket walking toward a distant warm orange bonfire glow on a dark horizon, vibrant amber firelight reflecting on his back and shoulders, leaving the dark past behind"
    },
    {
        "id": "10",
        "title": "Бридж. Вода",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a person in a soaked linen tunic standing chest-deep in calm misty lake water, taking a slow deliberate step forward into the dense silver fog, water rippling softly at shoulder level, hauntingly quiet courage"
    },
    {
        "id": "11",
        "title": "Лестница",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a barefoot woman in a dark tailored trouser suit climbing a tall exterior industrial steel fire escape staircase, holding her shoes in one hand, stepping firmly upward rung by rung, urban skyline blurred in the warm background, relentless drive to live"
    },
    {
        "id": "12",
        "title": "Бег по камню",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Dynamic tracking shot from behind of an athletic man in simple running clothes sprinting uphill across rugged slate rock slopes, back muscles engaged, leaning hard into the ascent, raw kinetic determination"
    },
    {
        "id": "13",
        "title": "Склон в тумане",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Behind view of a solitary figure in a dark hooded rain cloak hiking up a steep grassy ridge entirely enveloped in thick mountain mist, invisible summit ahead, continuing to walk forward into the white unknown"
    },
    {
        "id": "14",
        "title": "Последний участок",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Low-angle shot from behind of an elderly grandmother with a straight proud spine, leaning on a wooden cane, taking deliberate patient steps uphill along a rocky path at golden twilight, unwavering resilient willpower"
    },
    {
        "id": "15",
        "title": "Вершина",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Extreme wide shot from behind of a man standing on the edge of a towering mountain rock ledge overlooking a majestic sea of golden clouds at sunset, arms wide open to the wind, triumphant silhouette against the immense sky, slow crane pull up"
    },
    {
        "id": "16",
        "title": "Поворот (Эхо вершин)",
        "prompt": "Cinematic 35mm film photograph, Kodak Portra 400 grain, authentic human documentary style, rich natural lighting, muted filmic tones, emotional storytelling, 16:9 widescreen composition, rear view, seen strictly from behind, no faces visible, directed by Andrey Tarkovsky and Roger Deakins | Breathtaking high-angle bird's eye panoramic shot looking down: dozens of diverse solitary people across an expansive cinematic landscape (on rooftops, hills, bridges, cliffs, riverbanks), all seen strictly from behind, all standing with arms outstretched embracing the wind, each standing on their own personal peak at golden hour, profoundly moving collective triumph"
    }
]

async def generate_all():
    api = AgnesImageAPI(get_api_key())
    total = len(SPINA_SCENES)
    
    print(f"=== Starting generation of {total} SPINA keyframes via AgnesImageAPI ===")
    
    for idx, sc in enumerate(SPINA_SCENES, 1):
        target_file = OUT_DIR / f"spina_{sc['id']}.png"
        if target_file.exists():
            print(f"[{idx}/{total}] Scene {sc['id']}: Already exists, skipping ({target_file.name})")
            continue
            
        print(f"\n[{idx}/{total}] Generating Scene {sc['id']}: {sc['title']}...")
        try:
            output = await api.generate_single_image(
                prompt=sc["prompt"],
                size="1344x768"
            )
            await output.save(str(target_file))
            print(f"  --> Saved: {target_file.name} ({target_file.stat().st_size} bytes)")
        except Exception as e:
            print(f"  [ERROR] Scene {sc['id']} failed: {e}")
            
        # Courtesy pause between image generations
        await asyncio.sleep(4)
        
    print("\n=== ALL SPINA KEYFRAMES COMPLETED! ===")

if __name__ == "__main__":
    asyncio.run(generate_all())
