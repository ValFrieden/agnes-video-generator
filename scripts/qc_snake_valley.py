import os
import shutil
import subprocess

SRC = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\CRITICAL_PHYSICAL_AND_BIOLOGICAL_REALISM_27038c9d.mp4"
DEST = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_snake_valley_v1.mp4"
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
ARTIFACT_VIDEO = os.path.join(ARTIFACT_DIR, "scene_snake_valley_v1.mp4")

# Copy to canonical name
shutil.copy2(SRC, DEST)
shutil.copy2(DEST, ARTIFACT_VIDEO)
print(f"Copied to {DEST} and {ARTIFACT_VIDEO}")

# Get duration with ffprobe
cmd_probe = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{DEST}"'
duration_str = subprocess.check_output(cmd_probe, shell=True).decode().strip()
duration = float(duration_str)
print(f"Video duration: {duration:.2f} seconds")

# Extract 25%, 50%, 75% frames
t25 = duration * 0.25
t50 = duration * 0.50
t75 = duration * 0.75

f25 = os.path.join(ARTIFACT_DIR, "qc_snake_valley_v1_25.png")
f50 = os.path.join(ARTIFACT_DIR, "qc_snake_valley_v1_50.png")
f75 = os.path.join(ARTIFACT_DIR, "qc_snake_valley_v1_75.png")
cs_path = os.path.join(ARTIFACT_DIR, "qc_scene_snake_valley_v1.png")

subprocess.run(f'ffmpeg -y -ss {t25:.2f} -i "{DEST}" -vframes 1 "{f25}"', shell=True, check=True)
subprocess.run(f'ffmpeg -y -ss {t50:.2f} -i "{DEST}" -vframes 1 "{f50}"', shell=True, check=True)
subprocess.run(f'ffmpeg -y -ss {t75:.2f} -i "{DEST}" -vframes 1 "{f75}"', shell=True, check=True)

# Build contact sheet: 3 images side by side
# Scale each to 640x360 and stack horizontally: total 1920x360
cmd_cs = (
    f'ffmpeg -y -i "{f25}" -i "{f50}" -i "{f75}" '
    f'-filter_complex "[0:v]scale=640:360[v0];[1:v]scale=640:360[v1];[2:v]scale=640:360[v2];[v0][v1][v2]hstack=inputs=3[out]" '
    f'-map "[out]" "{cs_path}"'
)
subprocess.run(cmd_cs, shell=True, check=True)

# Also copy frames to project folder
frames_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\qc"
os.makedirs(frames_dir, exist_ok=True)
shutil.copy2(f25, os.path.join(frames_dir, "qc_snake_valley_v1_25.png"))
shutil.copy2(f50, os.path.join(frames_dir, "qc_snake_valley_v1_50.png"))
shutil.copy2(f75, os.path.join(frames_dir, "qc_snake_valley_v1_75.png"))
shutil.copy2(cs_path, os.path.join(frames_dir, "qc_scene_snake_valley_v1.png"))

print("QC frames generated successfully!")
