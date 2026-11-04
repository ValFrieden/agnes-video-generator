import subprocess
import json

clips_info = []
for i in range(1, 17):
    name = f"clip_{i:02d}.mp4"
    path = f"d:/Projects/VideoGenerator/kuda_idu_frames/clips/{name}"
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration:format=duration",
        "-of", "json",
        path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(res.stdout)
    v_stream = data.get("streams", [{}])[0]
    dur = float(data.get("format", {}).get("duration", 0))
    w = v_stream.get("width")
    h = v_stream.get("height")
    fps = v_stream.get("r_frame_rate")
    clips_info.append({"clip": name, "dur": dur, "w": w, "h": h, "fps": fps})

print(f"{'Clip':<12} | {'Duration (s)':<12} | {'Resolution':<12} | {'FPS'}")
print("-" * 50)
total_dur = 0
for c in clips_info:
    res_str = f"{c['w']}x{c['h']}"
    print(f"{c['clip']:<12} | {c['dur']:<12.2f} | {res_str:<12} | {c['fps']}")
    total_dur += c['dur']

print("-" * 50)
print(f"Total raw duration of 16 clips: {total_dur:.2f} s")
