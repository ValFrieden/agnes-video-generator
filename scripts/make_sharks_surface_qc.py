import subprocess
import os
import shutil

video_path = r'd:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_sharks_surface.mp4'
out_dir = r'd:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips'
brain_dir = r'C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a'

# Probe video
cmd_probe = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height,r_frame_rate', '-of', 'json', video_path]
res = subprocess.check_output(cmd_probe).decode()
print("Video probe:", res)

# Extract 25%, 50%, 75% frames
f25 = os.path.join(out_dir, 'qc_shark_25.png')
f50 = os.path.join(out_dir, 'qc_shark_50.png')
f75 = os.path.join(out_dir, 'qc_shark_75.png')

subprocess.run(['ffmpeg', '-y', '-ss', '2.0', '-i', video_path, '-vframes', '1', f25], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg', '-y', '-ss', '4.0', '-i', video_path, '-vframes', '1', f50], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg', '-y', '-ss', '6.0', '-i', video_path, '-vframes', '1', f75], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Extracted individual QC frames.")

# Create horizontal strip contact sheet: 25% | 50% | 75%
qc_sheet = os.path.join(out_dir, 'qc_scene_sharks_surface.png')
filter_complex = '[0:v][1:v][2:v]hstack=inputs=3[out]'
subprocess.run(['ffmpeg', '-y', '-i', f25, '-i', f50, '-i', f75, '-filter_complex', filter_complex, '-map', '[out]', qc_sheet], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Built contact sheet:", qc_sheet)

# Copy to brain artifacts
dst_brain = os.path.join(brain_dir, 'qc_scene_sharks_surface.png')
shutil.copy2(qc_sheet, dst_brain)
shutil.copy2(f25, os.path.join(brain_dir, 'qc_shark_25.png'))
shutil.copy2(f50, os.path.join(brain_dir, 'qc_shark_50.png'))
shutil.copy2(f75, os.path.join(brain_dir, 'qc_shark_75.png'))
print("Copied to brain artifacts successfully!")
