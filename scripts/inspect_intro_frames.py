import subprocess
from pathlib import Path

OUT_DIR = Path("C:/Users/Valeri/.gemini/antigravity-ide/brain/a184086b-b003-494b-a42d-1bb6fbd2a207/.tempmediaStorage/intro_frames")
OUT_DIR.mkdir(exist_ok=True)

vid_path = Path("d:/Projects/VideoGenerator/begi_za_solntsem_frames/Беги_за_солнцем_Финал_Flow_Veo.mp4")

# Extract 1 frame per second for the first 18 seconds
cmd = [
    "ffmpeg", "-y", "-ss", "00:00:00", "-to", "00:00:18",
    "-i", str(vid_path),
    "-vf", "fps=1,scale=640:360",
    str(OUT_DIR / "frame_%02d.jpg")
]
subprocess.run(cmd, capture_output=True)
print("Frames extracted to:", OUT_DIR)
