import cv2
from PIL import Image
from pathlib import Path

source = Path("door_frames/MAP_CHARACTER_MAN.jpg")
im = Image.open(source)
print("Source dimensions:", im.size)

# В MAP_CHARACTER_MAN лицо находится в верхней центральной части
# Делаем плотный портретный кроп лица
w, h = im.size
# Точные координаты лица
box = (int(w * 0.38), int(h * 0.12), int(w * 0.62), int(h * 0.52))
face_crop = im.crop(box)
print("Cropped face size:", face_crop.size)

# Сохраняем эталонный мастер-портрет лица
face_crop.save("references/character_valeri_face_master.jpg", quality=95)

brain_dir = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
face_crop.save(brain_dir / "character_valeri_face_master.jpg", quality=95)
print("Saved character_valeri_face_master.jpg to references and brain!")
