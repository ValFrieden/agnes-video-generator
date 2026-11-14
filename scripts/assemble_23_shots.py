import subprocess
import os
import shutil

OUTPUT_DIR = r"d:\Projects\VideoGenerator\output"
ART_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66"
AUDIO_PATH = os.path.join(ART_DIR, ".user_uploaded", "uploaded_media_1793789661300.mp3")

# All 23 completed shots
shots = [
    os.path.join(OUTPUT_DIR, f"shot_{i:02d}_{suffix}.mp4")
    for i, suffix in [
        (1, "single_panel"),
        (2, "room_cube"),
        (3, "sealed_cube"),
        (4, "light_burst"),
        (5, "dense_mist"),
        (6, "condensation_drips"),
        (7, "paper_sags"),
        (8, "water_reflection"),
        (9, "cracking_cube"),
        (10, "smoldering_embers"),
        (11, "walls_to_ash"),
        (12, "emerald_sprout"),
        (13, "blossomed_flower"),
        (14, "airborne_dew"),
        (15, "wide_lake"),
        (16, "open_horizon"),
        (17, "dew_prisms"),
        (18, "mirror_ripples"),
        (19, "swaying_flower"),
        (20, "glide_horizon"),
        (21, "ember_vortex"),
        (22, "tear_veil"),
        (23, "blazing_sunrise"),
    ]
]

for s in shots:
    if not os.path.exists(s):
        print(f"MISSING: {s}")

list_path = os.path.join(OUTPUT_DIR, "all_23_shots_list.txt")
with open(list_path, "w", encoding="utf-8") as f:
    for s in shots:
        escaped = s.replace("\\", "/")
        f.write(f"file '{escaped}'\n")

raw_23 = os.path.join(OUTPUT_DIR, "master_23_shots_visuals.mp4")
cmd_concat = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", list_path,
    "-c", "copy",
    raw_23
]
subprocess.run(cmd_concat, check=True)

# Probe duration
probe_cmd = [
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    raw_23
]
v_duration = float(subprocess.check_output(probe_cmd).decode().strip())
print(f"Total video duration for 23 shots: {v_duration:.2f}s")

# Mux with original audio
master_23 = os.path.join(OUTPUT_DIR, "metamorfoza_materii_master_23_shots.mp4")
cmd_mux = [
    "ffmpeg", "-y",
    "-i", raw_23,
    "-i", AUDIO_PATH,
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "192k",
    "-t", str(v_duration),
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-shortest",
    master_23
]
subprocess.run(cmd_mux, check=True)
shutil.copyfile(master_23, os.path.join(ART_DIR, "metamorfoza_materii_master_23_shots.mp4"))
print(f"Master 23 shots video assembled: {master_23}")
