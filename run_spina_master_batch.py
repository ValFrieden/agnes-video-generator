import os
import sys
import asyncio
from pathlib import Path
from core.api.google_flow_engine import GoogleFlowEngine

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path('d:/Projects/VideoGenerator').resolve()
FRAMES_DIR = PROJECT_ROOT / 'kuda_idu_frames'
CLIPS_DIR = FRAMES_DIR / 'clips'
PROMPTS_FILE = FRAMES_DIR / 'motion_prompts.txt'

CLIPS_DIR.mkdir(parents=True, exist_ok=True)

# Lade Motion Prompts
MOTION_PROMPTS = {}
if PROMPTS_FILE.exists():
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    MOTION_PROMPTS[parts[0].strip()] = parts[2].strip()

async def main():
    start_scene = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    end_scene = int(sys.argv[2]) if len(sys.argv) > 2 else 16

    print("\n" + "=" * 60)
    print(f"🚀 MASTER BATCH GENERATOR (GoogleFlowEngine): SCENES {start_scene} TO {end_scene}")
    print("=" * 60 + "\n")

    engine = GoogleFlowEngine()
    try:
        await engine.connect()

        for s in range(start_scene, end_scene + 1):
            s_str = f"{s:02d}"
            final_clip = CLIPS_DIR / f"clip_{s_str}.mp4"
            ref_img = FRAMES_DIR / f"spina_{s_str}.png"
            motion_prompt = MOTION_PROMPTS.get(s_str, '')

            print(f"\n🎬 [Scene {s_str}] Starting production...")
            print(f"   Ref Image: {ref_img if ref_img.exists() else 'None'}")
            print(f"   Prompt:    {motion_prompt}")

            success = await engine.generate_scene(
                prompt=motion_prompt,
                reference_image_path=str(ref_img) if ref_img.exists() else None,
                output_clip_path=str(final_clip),
                style_suffix="Authentic 35mm film still, Kodak Portra 400 grain, Roger Deakins natural lighting, human documentary realism, quiet emotion, 16:9 widescreen",
                skip_if_exists=True,
                max_retries=2,
            )

            if success:
                print(f"✅ [Scene {s_str}] Successfully completed: {final_clip}")
            else:
                print(f"❌ [Scene {s_str}] Failed after retries.")

            await asyncio.sleep(3.0)

    finally:
        await engine.close()

    print("\n🏁 ALL SCENES FINISHED!\n")

if __name__ == '__main__':
    asyncio.run(main())
