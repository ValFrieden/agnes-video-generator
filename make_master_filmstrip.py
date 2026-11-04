import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

VIDEO_PATH = 'd:/Projects/VideoGenerator/Мой_Мир_Из_Снов_FINAL_1080p.mp4'
TEMP_DIR = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/temp_filmstrip'
os.makedirs(TEMP_DIR, exist_ok=True)

timestamps = [
    ('Сцена 01 (00:03)', 3.6),
    ('Сцена 02 (00:10)', 10.8),
    ('Сцена 03 (00:18)', 18.0),
    ('Сцена 04 (00:25)', 25.2),
    ('Сцена 05 (00:32)', 32.5),
    ('Сцена 06 (00:39)', 39.7),
    ('Сцена 07 (00:46)', 46.9),
    ('Сцена 08 (00:54)', 54.1),
    ('Сцена 09 (00:61)', 61.4),
    ('Сцена 10 (00:68)', 68.6),
    ('Сцена 11 (00:76)', 76.0),
]

frames = []
for idx, (title, ts) in enumerate(timestamps, 1):
    out_img = os.path.join(TEMP_DIR, f'f_{idx:02d}.jpg')
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(ts),
        '-i', VIDEO_PATH,
        '-vframes', '1',
        '-q:v', '2',
        out_img
    ]
    subprocess.run(cmd, capture_output=True)
    img = Image.open(out_img).convert('RGB').resize((480, 270))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (220, 38)], fill=(0, 0, 0, 190))
    draw.text((16, 14), title, fill=(255, 230, 0))
    frames.append(img)

# 3 rows x 4 cols (12 slots, 11 scenes + 1 title card)
grid_w = 480 * 4
grid_h = 270 * 3
canvas = Image.new('RGB', (grid_w, grid_h), color=(15, 18, 25))

for i, img in enumerate(frames):
    r = i // 4
    c = i % 4
    canvas.paste(img, (c * 480, r * 270))

# 12th slot: Info Card
slot12 = Image.new('RGB', (480, 270), color=(20, 25, 35))
draw12 = ImageDraw.Draw(slot12)
draw12.text((30, 40), 'МОЙ МИР ИЗ СНОВ', fill=(255, 230, 100))
draw12.text((30, 75), 'МОИХ МЕЧТАНИЙ', fill=(255, 230, 100))
draw12.text((30, 120), 'Full 1080p Master Clip', fill=(200, 220, 255))
draw12.text((30, 150), '11 / 11 Scenes Approved', fill=(100, 255, 150))
draw12.text((30, 180), 'Duration: 01:20 (133 BPM)', fill=(220, 220, 220))
draw12.text((30, 210), 'Makoto Shinkai CoMix Wave', fill=(180, 180, 200))
canvas.paste(slot12, (3 * 480, 2 * 270))

out_filmstrip = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/master_mv_filmstrip.jpg'
canvas.save(out_filmstrip, quality=95)

art_filmstrip = 'C:/Users/Valeri/.gemini/antigravity-ide/brain/fc06ecd3-9c4c-48f1-8ce0-810057a8141e/master_mv_filmstrip.jpg'
canvas.save(art_filmstrip, quality=95)
print('Saved master filmstrip to', out_filmstrip)
