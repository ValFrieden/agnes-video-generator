import os
import subprocess
from pathlib import Path

CLIPS_DIR = Path("d:/Projects/VideoGenerator/begi_za_solntsem_frames/clips_flow_v2")
OUT_THUMBS = Path("d:/Projects/VideoGenerator/begi_za_solntsem_frames/thumbs_flow_v2")
OUT_THUMBS.mkdir(exist_ok=True)

files = sorted(list(CLIPS_DIR.glob("scene_tile_*.mp4")))
print(f"Total downloaded files: {len(files)}")

tile_reports = []

for f in files:
    # 1. Get duration and resolution
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,nb_frames",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(f)
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    lines = res.stdout.strip().split("\n")
    w = lines[0] if len(lines) > 0 else "?"
    h = lines[1] if len(lines) > 1 else "?"
    dur = lines[2] if len(lines) > 2 else "?"
    
    # 2. Extract mid frame
    thumb_path = OUT_THUMBS / f"{f.stem}.jpg"
    thumb_cmd = [
        "ffmpeg", "-y", "-ss", "00:00:03.000",
        "-i", str(f), "-vframes", "1",
        "-vf", "scale=640:-1",
        str(thumb_path)
    ]
    subprocess.run(thumb_cmd, capture_output=True)

    tile_reports.append({
        "file": f.name,
        "size_mb": round(f.stat().st_size / (1024*1024), 2),
        "resolution": f"{w}x{h}",
        "duration": dur,
        "thumb": str(thumb_path)
    })

print("\n--- Summary ---")
for r in tile_reports:
    print(f"{r['file']}: {r['size_mb']} MB, {r['resolution']}, {r['duration']}s -> {r['thumb']}")

# 3. Create a composite montage sheet (4x3 grid)
grid_cmd = [
    "ffmpeg", "-y",
    "-pattern_type", "glob", "-i", str(OUT_THUMBS / "scene_tile_*.jpg"),
    "-vf", "tile=4x3",
    str(OUT_THUMBS / "montage_all_tiles.jpg")
]
subprocess.run(grid_cmd, capture_output=True)
print("Montage created at:", OUT_THUMBS / "montage_all_tiles.jpg")
