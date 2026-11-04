"""Montage: clips trimmed to script durations + song. S17 missing -> freeze of S16 last frame (placeholder)."""
import re
import subprocess
from pathlib import Path

ROOT = Path("D:/Projects/VideoGenerator")
SCRIPT = ROOT / "С днём рождения, Маша — сценарий клипа (Google Flow).md"
CLIPS = ROOT / "masha_frames/clips"
OUT_DIR = ROOT / "masha_frames/montage"
SONG = Path("C:/Users/Valeri/Downloads/Masha - S dnem Rozdenija.mp3")
OUT = OUT_DIR / "masha_clip_v4.mp4"
SONG_LEN = 187.0

dur = {}
for line in SCRIPT.read_text(encoding="utf-8").splitlines():
    m = re.match(r"\|\s*S(\d\d)\s*\|[^|]*\|\s*(\d+)s\s*\|", line)
    if m:
        dur[int(m.group(1))] = int(m.group(2))

# (label, source clip, seconds). S01 = ffmpeg-морфинг фото->3D (НЕ clip_01), S17 = новый клип 8 с (без стоп-кадров),
# S19 играет свои 8 с (в сценарии 10): +2 с у S17 и -2 с у S19 сохраняют синхрон с песней.
parts = []
for n in range(1, 26):
    if n == 1:
        parts.append(("S01 морфинг", ROOT / "masha_frames/morph/morph_s01_slow.mp4", dur[1]))
    elif n == 17:
        parts.append(("S17 новый клип", CLIPS / "clip_17.mp4", 8))
    elif n == 19:
        parts.append(("S19", CLIPS / "clip_19.mp4", 8))
    else:
        parts.append((f"S{n:02d}", CLIPS / f"clip_{n:02d}.mp4", dur[n]))
parts.append(("S27 (фея, подарок)", CLIPS / "clip_27.mp4", 8))
parts.append(("S28 (торт, затемнение)", CLIPS / "clip_28.mp4", 8))
for label, path, secs in parts:
    if not path.exists():
        raise SystemExit(f"нет файла для {label}: {path}")

OUT_DIR.mkdir(parents=True, exist_ok=True)
inputs, filters, labels = [], [], []
t = 0.0
for i, (label, path, secs) in enumerate(parts):
    inputs += ["-i", str(path)]
    filters.append(f"[{i}:v]fps=24,scale=1280:720,setsar=1,trim=duration={secs},setpts=PTS-STARTPTS[v{i}]")
    labels.append(f"[v{i}]")
    print(f"{t:6.1f}s  {label}  {secs}s")
    t += secs
print("итого видео:", t, "c; песня:", SONG_LEN)

fc = ";".join(filters) + ";" + "".join(labels) + f"concat=n={len(parts)}:v=1:a=0[vout]"
cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", str(SONG),
       "-filter_complex", fc, "-map", "[vout]", "-map", f"{len(parts)}:a",
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-t", str(min(t, SONG_LEN)), str(OUT)]
subprocess.run(cmd, check=True)
print("готово:", OUT)
