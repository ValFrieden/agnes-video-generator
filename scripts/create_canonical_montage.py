import subprocess
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BASE_DIR = Path("d:/Projects/VideoGenerator/begi_za_solntsem_frames")
FINAL_DIR = BASE_DIR / "final_scenes"
TMP_THUMBS = BASE_DIR / "canonical_thumbs"
TMP_THUMBS.mkdir(exist_ok=True)
OUT_POSTER = Path("C:/Users/Valeri/.gemini/antigravity-ide/brain/a184086b-b003-494b-a42d-1bb6fbd2a207/.tempmediaStorage/canonical_storyboard_poster.jpg")

SCENES = [
    ("scene_01_intro_bench.mp4", "01. Интро: 00:00–00:08", "Скамья, дождь, закрытый зонт"),
    ("scene_02_umbrella_pickup.mp4", "02. Подъем: 00:08–00:16", "Путник со спины у скамьи"),
    ("scene_03_puddle_sunbeam.mp4", "03. Капли: 00:16–00:24", "Брусчатка, лужа, луч солнца"),
    ("scene_04_stone_alley.mp4", "04. Переулок: 00:24–00:32", "Каменный переулок, луч"),
    ("scene_05_attic_window.mp4", "05. Окно: 00:32–00:40", "Окно с золотым светом"),
    ("scene_06_stone_bridge.mp4", "06. Мост: 00:40–00:48", "Мост на стыке туч и рассвета"),
    ("scene_07_face_closeup.mp4", "07. Крупный план: 00:48–00:56", "Лицо в профиль, капля"),
    ("scene_08_arched_colonnade.mp4", "08. Колоннада: 00:56–01:04", "Колоннада, зонт-факел"),
    ("scene_09_river_promenade.mp4", "09. Набережная: 01:04–01:12", "Зонт-щит, золотые лучи"),
    ("scene_10_cathedral_spires.mp4", "10. Шпили: 01:12–01:20", "Собор, свет сквозь тучи"),
    ("scene_11_rooftop_panorama.mp4", "11. Панорама: 01:20–01:28", "Терраса крыши на рассвете"),
    ("scene_12_outro_park_sun.mp4", "12. Финал: 01:28–01:36", "Летний парк, солнце, надежда")
]

w, h = 480, 270
cols, rows = 4, 3
canvas = Image.new("RGB", (cols * w, rows * h), color=(15, 15, 18))
draw = ImageDraw.Draw(canvas)

for idx, (filename, title, subtitle) in enumerate(SCENES):
    vid_path = FINAL_DIR / filename
    thumb_path = TMP_THUMBS / f"{vid_path.stem}.jpg"
    
    # Extract middle frame (00:00:04.0)
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:04.000",
        "-i", str(vid_path), "-vframes", "1",
        "-vf", "scale=480:270",
        str(thumb_path)
    ]
    subprocess.run(cmd, capture_output=True)

    img = Image.open(thumb_path)
    c = idx % cols
    r = idx // cols
    x = c * w
    y = r * h
    canvas.paste(img, (x, y))

    # Top overlay header
    draw.rectangle([x + 8, y + 8, x + 240, y + 36], fill=(0, 0, 0, 190))
    draw.text((x + 14, y + 14), title, fill=(255, 215, 0))

canvas.save(OUT_POSTER, quality=92)
print("Canonical storyboard poster created at:", OUT_POSTER)
