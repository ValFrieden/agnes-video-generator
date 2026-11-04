import subprocess
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


AUDIO_PATH = r"D:\Projects\VideoGenerator\Мои стихи\Куда иду зачем откуда.mp3"
CLIPS_DIR = r"D:\Projects\VideoGenerator\kuda_idu_frames\clips"
TEMP_DIR = r"D:\Projects\VideoGenerator\kuda_idu_frames\assembly_temp"
OUTPUT_MV = r"D:\Projects\VideoGenerator\kuda_idu_frames\Куда_иду_зачем_откуда_СПИНА_Master_MV.mp4"

os.makedirs(TEMP_DIR, exist_ok=True)

# Scene target durations in seconds (136 BPM measure-aligned)
# 6 bars = 10.588s, 4 bars = 7.059s, 8 bars = 14.118s
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
    (16, 23.239),  # Finale until 182.04s
]

total_target = sum(t[1] for t in SCENE_TIMINGS)
print(f"Target total video duration: {total_target:.3f} s (Audio duration: 182.04 s)")

prepared_clips = []
concat_list_path = os.path.join(TEMP_DIR, "concat_list.txt")

with open(concat_list_path, "w", encoding="utf-8") as f_list:
    for scene_num, target_dur in SCENE_TIMINGS:
        raw_clip = os.path.join(CLIPS_DIR, f"clip_{scene_num:02d}.mp4")
        out_clip = os.path.join(TEMP_DIR, f"scene_{scene_num:02d}_timed.mp4")

        # For scene 16: smooth continuous slow-motion across the entire finale (NO freeze frame!), fade to black in last 3s
        if scene_num == 16:
            scale_factor = target_dur / 8.0
            filter_str = (
                f"setpts={scale_factor:.6f}*PTS,fps=24,"
                f"trim=duration={target_dur:.3f},"
                f"fade=t=out:st={target_dur - 3.0:.3f}:d=3.0"
            )
        elif scene_num == 15:
            # 8s -> 14.118s
            scale_factor = target_dur / 8.0
            filter_str = f"setpts={scale_factor:.6f}*PTS,fps=24,trim=duration={target_dur:.3f}"
        elif scene_num == 9:
            # 8s -> 7.059s
            scale_factor = target_dur / 8.0
            filter_str = f"setpts={scale_factor:.6f}*PTS,fps=24,trim=duration={target_dur:.3f}"
        else:
            # 8s -> 10.588s
            scale_factor = target_dur / 8.0
            filter_str = f"setpts={scale_factor:.6f}*PTS,fps=24,trim=duration={target_dur:.3f}"

        cmd = [
            "ffmpeg", "-y",
            "-i", raw_clip,
            "-vf", filter_str,
            "-an",
            "-c:v", "libx264",
            "-crf", "17",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            out_clip
        ]
        print(f"Processing Scene {scene_num:02d} -> target: {target_dur:.3f}s...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        f_list.write(f"file '{out_clip.replace(os.sep, '/')}'\n")

print("\nAll 16 scenes timed and prepared!")

# Concat video stream and merge with original music
temp_video_only = os.path.join(TEMP_DIR, "video_concat.mp4")
print("Concatenating 16 video scenes...")
concat_cmd = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_list_path,
    "-c", "copy",
    temp_video_only
]
subprocess.run(concat_cmd, check=True)

print("Merging audio and rendering final master music video...")
# Merge with master audio track, apply subtle audio fade-out at very end
final_cmd = [
    "ffmpeg", "-y",
    "-i", temp_video_only,
    "-i", AUDIO_PATH,
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "256k",
    "-af", "afade=t=out:st=179.5:d=2.5",
    "-shortest",
    OUTPUT_MV
]
subprocess.run(final_cmd, check=True)

print(f"\n Master Music Video successfully assembled at:\n{OUTPUT_MV}")

# Probe final video
probe_cmd = [
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration,size:stream=width,height,r_frame_rate",
    "-of", "json",
    OUTPUT_MV
]
res = subprocess.run(probe_cmd, capture_output=True, text=True)
print("Final Video Info:", res.stdout)
