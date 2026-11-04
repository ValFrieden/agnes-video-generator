import cv2
import os

FRAMES_DIR = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"
s04 = cv2.imread(os.path.join(FRAMES_DIR, "anime_s04_qa_50.jpg"))
s03 = cv2.imread(os.path.join(FRAMES_DIR, "anime_s03_qa_50.jpg"))

# Let's save 10 candidate crops for Valeri s04
for dx in range(300, 500, 40):
    for dy in range(100, 260, 40):
        sub = s04[dy:dy+140, dx:dx+140]
        cv2.imwrite(os.path.join(FRAMES_DIR, f"test_v_s04_{dx}_{dy}.jpg"), sub)
print("Saved candidate crops.")
