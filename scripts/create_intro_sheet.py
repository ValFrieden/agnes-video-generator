from PIL import Image, ImageDraw
from pathlib import Path

DIR = Path("C:/Users/Valeri/.gemini/antigravity-ide/brain/a184086b-b003-494b-a42d-1bb6fbd2a207/.tempmediaStorage/intro_frames")
OUT_IMG = Path("C:/Users/Valeri/.gemini/antigravity-ide/brain/a184086b-b003-494b-a42d-1bb6fbd2a207/.tempmediaStorage/intro_contact_sheet.jpg")

frames = sorted(list(DIR.glob("frame_*.jpg")))
cols = 4
rows = (len(frames) + cols - 1) // cols
w, h = 320, 180

canvas = Image.new("RGB", (cols * w, rows * h), color=(10, 10, 10))
draw = ImageDraw.Draw(canvas)

for idx, f in enumerate(frames):
    img = Image.open(f).resize((w, h))
    c = idx % cols
    r = idx // cols
    x = c * w
    y = r * h
    canvas.paste(img, (x, y))
    draw.rectangle([x + 5, y + 5, x + 85, y + 25], fill=(0, 0, 0, 180))
    draw.text((x + 8, y + 8), f"{idx}s ({f.stem})", fill=(255, 255, 0))

canvas.save(OUT_IMG, quality=90)
print("Saved contact sheet:", OUT_IMG)
