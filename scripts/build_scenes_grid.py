import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

frames_dir = Path("nikogda_ne_boyus_frames")
scenes = [frames_dir / f"scene_{i:02d}.png" for i in range(1, 19)]

# Check if all exist
existing = [f for f in scenes if f.exists()]
print(f"Found {len(existing)} scenes out of 18.")

cols = 3
rows = 6
cell_w = 448  # 1344 // 3
cell_h = 256  # 768 // 3

grid = Image.new("RGB", (cols * cell_w, rows * cell_h + 40), (20, 20, 25))
draw = ImageDraw.Draw(grid)

for idx, scene_path in enumerate(scenes):
    if not scene_path.exists():
        continue
    c = idx % cols
    r = idx // cols
    im = Image.open(scene_path).resize((cell_w, cell_h), Image.Resampling.LANCZOS)
    x = c * cell_w
    y = r * cell_h + 35
    grid.paste(im, (x, y))
    
    # Text badge
    draw.rectangle([x + 10, y + 10, x + 110, y + 32], fill=(0, 0, 0, 180))
    draw.text((x + 16, y + 12), f"Scene {idx+1:02d}", fill=(255, 215, 0))

draw.text((20, 10), "«НИКОГДА НЕ БОЮСЬ» — ПОЛНАЯ РАСКАДРОВКА (18 СЦЕН)", fill=(255, 255, 255))
out_sheet = frames_dir / "all_18_scenes_qc.png"
grid.save(out_sheet)
print(f"QC Grid saved to {out_sheet.resolve()} ({out_sheet.stat().st_size} bytes)")
