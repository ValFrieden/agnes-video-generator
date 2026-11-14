import subprocess
import os
import shutil

video_path = r'd:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_sharks_surface_v2.mp4'
out_dir = r'd:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips'
brain_dir = r'C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a'

# Extract 25%, 50%, 75% frames (at ~2.0s, 4.0s, 6.0s of 8s video)
f25 = os.path.join(out_dir, 'qc_shark_v2_25.png')
f50 = os.path.join(out_dir, 'qc_shark_v2_50.png')
f75 = os.path.join(out_dir, 'qc_shark_v2_75.png')

subprocess.run(['ffmpeg', '-y', '-ss', '2.0', '-i', video_path, '-vframes', '1', f25], check=True)
subprocess.run(['ffmpeg', '-y', '-ss', '4.0', '-i', video_path, '-vframes', '1', f50], check=True)
subprocess.run(['ffmpeg', '-y', '-ss', '6.0', '-i', video_path, '-vframes', '1', f75], check=True)
print("Extracted individual QC frames.")

# Create horizontal strip contact sheet: 25% | 50% | 75%
qc_sheet = os.path.join(out_dir, 'qc_scene_sharks_surface_v2.png')
filter_complex = '[0:v][1:v][2:v]hstack=inputs=3[out]'
subprocess.run(['ffmpeg', '-y', '-i', f25, '-i', f50, '-i', f75, '-filter_complex', filter_complex, '-map', '[out]', qc_sheet], check=True)
print("Built contact sheet:", qc_sheet)

# Copy to brain artifacts
shutil.copy2(qc_sheet, os.path.join(brain_dir, 'qc_scene_sharks_surface_v2.png'))
shutil.copy2(f25, os.path.join(brain_dir, 'qc_shark_v2_25.png'))
shutil.copy2(f50, os.path.join(brain_dir, 'qc_shark_v2_50.png'))
shutil.copy2(f75, os.path.join(brain_dir, 'qc_shark_v2_75.png'))
shutil.copy2(video_path, os.path.join(brain_dir, 'scene_sharks_surface_v2.mp4'))
print("Copied to brain artifacts successfully!")
