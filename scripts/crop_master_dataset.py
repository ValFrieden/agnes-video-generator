from PIL import Image
from pathlib import Path

out_dir = Path("nikogda_ne_boyus_frames")
img = Image.open(out_dir / "valeri_master_dataset.jpg")
w, h = img.size

# Черная полоса внизу начинается примерно на h - 55 = 516
crop_bottom = int(h * 0.90)  # ~514px

# 1. Центральный анфас
# Примерные границы по x: 340 до 680
front_box = (int(w * 0.34), 0, int(w * 0.68), crop_bottom)
front_crop = img.crop(front_box)
front_crop.save(out_dir / "valeri_ref_front.jpg", quality=95)
print("Saved valeri_ref_front.jpg:", front_crop.size)

# 2. Левый нижний профиль
profile_box = (0, int(h * 0.46), int(w * 0.33), crop_bottom)
profile_crop = img.crop(profile_box)
profile_crop.save(out_dir / "valeri_ref_profile.jpg", quality=95)
print("Saved valeri_ref_profile.jpg:", profile_crop.size)

# 3. Квадратный портрет лица для аватара и Face-Lock
# x: 360 .. 660, y: 10 .. 420
face_box = (int(w * 0.36), 10, int(w * 0.66), int(h * 0.75))
face_crop = img.crop(face_box)
face_crop.save(out_dir / "valeri_ref_face_square.jpg", quality=95)
print("Saved valeri_ref_face_square.jpg:", face_crop.size)
