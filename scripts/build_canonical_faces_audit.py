import os
from PIL import Image, ImageDraw, ImageFont

base_dir = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"
out_path = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames\canonical_faces_audit.jpg"

files = [
    ("Valeri Sheet", os.path.join(base_dir, "anime_character_valeri.png")),
    ("Scene 01", os.path.join(base_dir, "anime_scene_01.png")),
    ("Scene 02", os.path.join(base_dir, "anime_scene_02.png")),
    ("Scene 03", os.path.join(base_dir, "anime_scene_03.png")),
    ("Scene 04", os.path.join(base_dir, "anime_scene_04.png")),
    ("Elena Sheet", os.path.join(base_dir, "anime_character_elena.png")),
]

panels = []
target_h = 360

for label, p in files:
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("RGB")
    w, h = im.size
    new_w = int(w * (target_h / float(h)))
    im_resized = im.resize((new_w, target_h), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im_resized)
    draw.rectangle([(0, 0), (new_w, 36)], fill=(0, 0, 0))
    draw.text((10, 8), label, fill=(255, 255, 255))
    panels.append(im_resized)

if panels:
    total_w = sum(p.width for p in panels)
    canvas = Image.new("RGB", (total_w, target_h), (0, 0, 0))
    curr_x = 0
    for p in panels:
        canvas.paste(p, (curr_x, 0))
        curr_x += p.width
    canvas.save(out_path, quality=92)
    print("Saved audit to:", out_path)
