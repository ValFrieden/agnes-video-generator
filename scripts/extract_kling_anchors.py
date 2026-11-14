import subprocess
import os
import shutil

OUTPUT_DIR = r"d:\Projects\VideoGenerator\output"
REF_DIR = r"d:\Projects\VideoGenerator\references\kling_style_anchors"
os.makedirs(REF_DIR, exist_ok=True)
ART_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66"

anchors = [
    ("anchor_01_wet_dock_macro.png", os.path.join(OUTPUT_DIR, "shot_17_dew_prisms.mp4"), "2.5"),
    ("anchor_02_calm_lake_dawn.png", os.path.join(OUTPUT_DIR, "shot_20_glide_horizon.mp4"), "2.5"),
    ("anchor_03_liquid_gold_sun.png", os.path.join(OUTPUT_DIR, "shot_23_blazing_sunrise.mp4"), "4.5"),
]

for name, video_path, timestamp in anchors:
    out_ref = os.path.join(REF_DIR, name)
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", timestamp,
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "1",
        out_ref
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out_art = os.path.join(ART_DIR, name)
    shutil.copyfile(out_ref, out_art)
    print(f"Extracted {name} from {video_path} at {timestamp}s")

# Create a 3-panel anchor board image
board_path = os.path.join(REF_DIR, "kling_style_anchors_board.jpg")
cmd_board = [
    "ffmpeg", "-y",
    "-i", os.path.join(REF_DIR, "anchor_01_wet_dock_macro.png"),
    "-i", os.path.join(REF_DIR, "anchor_02_calm_lake_dawn.png"),
    "-i", os.path.join(REF_DIR, "anchor_03_liquid_gold_sun.png"),
    "-filter_complex", "[0:v]scale=640:360[v0];[1:v]scale=640:360[v1];[2:v]scale=640:360[v2];[v0][v1][v2]hstack=inputs=3[v]",
    "-map", "[v]",
    board_path
]
subprocess.run(cmd_board, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
shutil.copyfile(board_path, os.path.join(ART_DIR, "kling_style_anchors_board.jpg"))
print("Anchor board saved to:", board_path)
