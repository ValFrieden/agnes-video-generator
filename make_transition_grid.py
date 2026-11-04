from PIL import Image, ImageDraw

files = [
    ('S01 t=6.8s', 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/transition_s01_s02/s01_t6.8.jpg'),
    ('S01 t=7.0s', 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/transition_s01_s02/s01_t7.0.jpg'),
    ('S01 t=7.2s (CUT POINT)', 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/transition_s01_s02/s01_t7.2.jpg'),
    ('S02 t=0.0s (NEW SCENE)', 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/transition_s01_s02/s02_t0.0.jpg'),
    ('S02 t=0.2s', 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/transition_s01_s02/s02_t0.2.jpg'),
    ('S02 t=0.4s', 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/transition_s01_s02/s02_t0.4.jpg'),
]

canvas = Image.new('RGB', (1920, 720))

for idx, (lbl, fpath) in enumerate(files):
    img = Image.open(fpath).convert('RGB').resize((640, 360))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (300, 40)], fill=(0, 0, 0, 200))
    draw.text((15, 15), lbl, fill=(255, 230, 0))
    r = idx // 3
    c = idx % 3
    canvas.paste(img, (c * 640, r * 360))

out_path = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/transition_inspection.jpg'
canvas.save(out_path, quality=95)

art_path = 'C:/Users/Valeri/.gemini/antigravity-ide/brain/fc06ecd3-9c4c-48f1-8ce0-810057a8141e/transition_inspection.jpg'
canvas.save(art_path, quality=95)
print('Saved transition inspection')
