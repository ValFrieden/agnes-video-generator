"""Картинка мультяшной Маши (по листу) в позе и композиции живого фото: python scripts/generate_masha_toon_keyframe.py"""
import asyncio, importlib, sys, types
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
for n, s in (("core", ROOT / "core"), ("core.api", ROOT / "core" / "api")):
    m = types.ModuleType(n); m.__path__ = [str(s)]; sys.modules[n] = m
Engine = importlib.import_module("core.api.google_flow_engine").GoogleFlowEngine
PHOTO = ROOT / "masha_frames/ref/s01_photo_16x9_crop.jpg"
SHEET = ROOT / "masha_frames/old_project/01_turnaround.jpg"
OUT = ROOT / "masha_frames/ref/s01_toon_keyframe_v1.png"
PROMPT = (
    "Generate one image (not a video), 16:9 landscape widescreen. The first image is a real photograph, "
    "the second image is the character sheet of the animated heroine Masha. Redraw the photograph as "
    "animated Masha from the sheet: her exact face, brown eyes, long dark-brown hair and 3D Pixar-like style, "
    "wearing her light-blue shirt. Keep the EXACT same composition as the photo: same position and scale, "
    "head tilted the same way, cheek resting on her fist, same smile with closed mouth, same grey stone steps "
    "and sunglasses on her head. No text, no caption, no name label, no watermark."
)
async def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    e = Engine(downloads_dir=str(OUT.parent))
    await e.connect()
    p = await e.generate_image(PROMPT, references=[str(PHOTO), str(SHEET)], output_path=str(OUT))
    print("OK", p)
asyncio.run(main())
