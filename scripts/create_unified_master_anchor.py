import os
from PIL import Image, ImageDraw, ImageFont

base_dir = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"
out_master = os.path.join(base_dir, "UNIFIED_CANON_ANCHOR_REF.png")

# Load Scene 03 (close up of both) and Scene 04 (full body walking)
s03 = Image.open(os.path.join(base_dir, "anime_scene_03.png")).convert("RGB")
s04 = Image.open(os.path.join(base_dir, "anime_scene_04.png")).convert("RGB")
s01 = Image.open(os.path.join(base_dir, "anime_scene_01.png")).convert("RGB")

# Crop Valeri face from Scene 03 (x: 520 to 620, y: 130 to 250 in 1280x720)
# Let's inspect coordinates of Valeri in Scene 03:
# Scene 03 is 1280x720. Valeri is on the left half (around x=500 to 750)
w3, h3 = s03.size

# In Scene 03: Valeri is roughly x: 500-750, y: 100-450
valeri_s03_crop = s03.crop((int(w3 * 0.42), int(h3 * 0.12), int(w3 * 0.58), int(h3 * 0.55)))

# Elena in Scene 03: roughly x: 580-780, y: 120-550
elena_s03_crop = s03.crop((int(w3 * 0.58), int(h3 * 0.15), int(w3 * 0.75), int(h3 * 0.65)))

# Valeri from Scene 01: center figure
w1, h1 = s01.size
valeri_s01_crop = s01.crop((int(w1 * 0.60), int(h1 * 0.25), int(w1 * 0.72), int(h1 * 0.60)))

# Resize crops to standard height 400
target_h = 400
v3_resized = valeri_s03_crop.resize((int(valeri_s03_crop.width * (target_h / valeri_s03_crop.height)), target_h), Image.Resampling.LANCZOS)
e3_resized = elena_s03_crop.resize((int(elena_s03_crop.width * (target_h / elena_s03_crop.height)), target_h), Image.Resampling.LANCZOS)
v1_resized = valeri_s01_crop.resize((int(valeri_s01_crop.width * (target_h / valeri_s01_crop.height)), target_h), Image.Resampling.LANCZOS)

# Also s04 full couple resized
s04_resized = s04.resize((int(s04.width * (target_h / s04.height)), target_h), Image.Resampling.LANCZOS)

# Build a clean side-by-side reference board
board_w = v1_resized.width + v3_resized.width + e3_resized.width + s04_resized.width
board = Image.new("RGB", (board_w, target_h + 60), (20, 20, 22))

curr_x = 0
items = [
    (v1_resized, "Valeri S01 (Canon Face)"),
    (v3_resized, "Valeri S03 (Canon Profile)"),
    (e3_resized, "Elena S03 (Canon Hair & Face)"),
    (s04_resized, "Scene 04 (Locked Outfits & Scale)")
]

draw = ImageDraw.Draw(board)
for img, label in items:
    board.paste(img, (curr_x, 60))
    draw.rectangle([(curr_x, 0), (curr_x + img.width - 2, 58)], fill=(35, 35, 40))
    draw.text((curr_x + 10, 20), label, fill=(240, 240, 240))
    curr_x += img.width

board.save(out_master, quality=95)
print("Saved UNIFIED_CANON_ANCHOR_REF.png to:", out_master)
