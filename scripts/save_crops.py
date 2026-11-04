import cv2
import os

FRAMES_DIR = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"
s04 = cv2.imread(os.path.join(FRAMES_DIR, "anime_s04_qa_50.jpg"))
s03 = cv2.imread(os.path.join(FRAMES_DIR, "anime_s03_qa_50.jpg"))

# Let's save candidate crops around x=450, y=140 for Valeri S04, and x=650, y=200 for Elena S04
cv2.imwrite(os.path.join(FRAMES_DIR, "crop_v_s04.jpg"), s04[130:330, 430:610])
cv2.imwrite(os.path.join(FRAMES_DIR, "crop_e_s04.jpg"), s04[210:410, 620:790])

# For S03:
cv2.imwrite(os.path.join(FRAMES_DIR, "crop_v_s03.jpg"), s03[80:300, 360:550])
cv2.imwrite(os.path.join(FRAMES_DIR, "crop_e_s03.jpg"), s03[190:400, 660:830])
print("Saved 4 crops.")
