from PIL import Image, ImageDraw

p1 = Image.open('d:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_07.png').convert('RGB').resize((640, 360))
p2 = Image.open('d:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_s07_qa_25.jpg').convert('RGB').resize((640, 360))
p3 = Image.open('d:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_s07_qa_50.jpg').convert('RGB').resize((640, 360))
p4 = Image.open('d:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_s07_qa_75.jpg').convert('RGB').resize((640, 360))

canvas = Image.new('RGB', (1280, 720))
canvas.paste(p1, (0, 0))
canvas.paste(p2, (640, 0))
canvas.paste(p3, (0, 360))
canvas.paste(p4, (640, 360))

draw = ImageDraw.Draw(canvas)
draw.rectangle([(10, 10), (320, 45)], fill=(0, 0, 0, 190))
draw.text((20, 20), 'ORIGINAL CANONICAL REF', fill=(255, 230, 0))

draw.rectangle([(650, 10), (840, 45)], fill=(0, 0, 0, 190))
draw.text((660, 20), 'QA 25% (2.0s)', fill=(255, 230, 0))

draw.rectangle([(10, 370), (200, 405)], fill=(0, 0, 0, 190))
draw.text((20, 380), 'QA 50% (4.0s)', fill=(255, 230, 0))

draw.rectangle([(650, 370), (840, 405)], fill=(0, 0, 0, 190))
draw.text((660, 380), 'QA 75% (6.0s)', fill=(255, 230, 0))

out_path = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/s07_remake_qa_review_grid.jpg'
canvas.save(out_path, quality=95)

art_path = 'C:/Users/Valeri/.gemini/antigravity-ide/brain/fc06ecd3-9c4c-48f1-8ce0-810057a8141e/s07_remake_qa_review_grid.jpg'
canvas.save(art_path, quality=95)
print('Saved grid to', out_path)
