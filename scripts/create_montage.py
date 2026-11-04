from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

THUMBS_DIR = Path("d:/Projects/VideoGenerator/begi_za_solntsem_frames/thumbs_flow_v2")
OUT_MONTAGE = Path("C:/Users/Valeri/.gemini/antigravity-ide/brain/a184086b-b003-494b-a42d-1bb6fbd2a207/.tempmediaStorage/montage_12_scenes.jpg")

files = sorted(list(THUMBS_DIR.glob("scene_tile_*.jpg")))
print(f"Found {len(files)} thumbnails")

cols = 4
rows = 3
w, h = 480, 270

canvas = Image.new("RGB", (cols * w, rows * h), color=(20, 20, 20))
draw = ImageDraw.Draw(canvas)

for idx, f in enumerate(files[:12]):
    img = Image.open(f).resize((w, h), Image.Resampling.LANCZOS)
    c = idx % cols
    r = idx // cols
    x = c * w
    y = r * h
    canvas.paste(img, (x, y))
    # Draw label box
    draw.rectangle([x + 10, y + 10, x + 160, y + 36], fill=(0, 0, 0, 180))
    draw.text((x + 15, y + 14), f"Tile {idx:02d}: {f.stem}", fill=(255, 255, 255))

canvas.save(OUT_MONTAGE, quality=90)
print(f"Saved montage to {OUT_MONTAGE}")
