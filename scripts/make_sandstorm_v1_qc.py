import subprocess
import os

video_path = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_sandstorm_haboob_v1.mp4"
output_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips"

# Extract 25% (2.0s), 50% (4.0s), 75% (6.0s)
t_list = [(2.0, "qc_sandstorm_v1_25.png"), (4.0, "qc_sandstorm_v1_50.png"), (6.0, "qc_sandstorm_v1_75.png")]

for t, name in t_list:
    out = os.path.join(output_dir, name)
    cmd = ["ffmpeg", "-ss", str(t), "-i", video_path, "-vframes", "1", "-y", out]
    subprocess.run(cmd, check=True)
    print("Extracted:", out)

# Build horizontal contact sheet
sheet_path = os.path.join(output_dir, "qc_scene_sandstorm_haboob_v1.png")
f25 = os.path.join(output_dir, "qc_sandstorm_v1_25.png")
f50 = os.path.join(output_dir, "qc_sandstorm_v1_50.png")
f75 = os.path.join(output_dir, "qc_sandstorm_v1_75.png")

cmd_sheet = [
    "ffmpeg",
    "-i", f25,
    "-i", f50,
    "-i", f75,
    "-filter_complex", "hstack=inputs=3",
    "-y", sheet_path
]
subprocess.run(cmd_sheet, check=True)
print("Created contact sheet:", sheet_path)
