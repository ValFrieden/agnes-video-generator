import subprocess
import os

MV_PATH = r"d:\Projects\VideoGenerator\kuda_idu_frames\kuda_idu_spina_master_mv.mp4"
TEMP_DIR = r"d:\Projects\VideoGenerator\kuda_idu_frames\assembly_temp\grid"
GRID_OUTPUT = r"d:\Projects\VideoGenerator\kuda_idu_frames\master_mv_16_scenes_grid.png"

os.makedirs(TEMP_DIR, exist_ok=True)

# Midpoint timestamps for each of the 16 scenes
SCENE_TIMINGS = [
    (1,  10.588),
    (2,  10.588),
    (3,  10.588),
    (4,  10.588),
    (5,  10.588),
    (6,  10.588),
    (7,  10.588),
    (8,  10.588),
    (9,  7.059),
    (10, 10.588),
    (11, 10.588),
    (12, 10.588),
    (13, 10.588),
    (14, 10.588),
    (15, 14.118),
    (16, 23.239),
]

current_t = 0.0
frame_files = []
for idx, (s_num, dur) in enumerate(SCENE_TIMINGS):
    mid_t = current_t + (dur / 2.0)
    current_t += dur
    frame_path = os.path.join(TEMP_DIR, f"scene_{s_num:02d}_mid.png")
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{mid_t:.2f}",
        "-i", MV_PATH,
        "-frames:v", "1",
        "-q:v", "2",
        frame_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    frame_files.append(frame_path)

# Build a 4x4 grid: 4 rows of 4 columns
# 1280x720 scaled to 480x270 each -> grid is 1920x1080
inputs = []
for f in frame_files:
    inputs.extend(["-i", f])

filter_parts = []
for i in range(16):
    filter_parts.append(f"[{i}:v]scale=480:270[v{i}];")

# 4 rows of 4
filter_parts.append(
    "[v0][v1][v2][v3]hstack=inputs=4[row0];"
    "[v4][v5][v6][v7]hstack=inputs=4[row1];"
    "[v8][v9][v10][v11]hstack=inputs=4[row2];"
    "[v12][v13][v14][v15]hstack=inputs=4[row3];"
    "[row0][row1][row2][row3]vstack=inputs=4[out]"
)
filter_complex = "".join(filter_parts)

grid_cmd = [
    "ffmpeg", "-y",
    *inputs,
    "-filter_complex", filter_complex,
    "-map", "[out]",
    GRID_OUTPUT
]
subprocess.run(grid_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Saved 16-scene master grid:", GRID_OUTPUT)
