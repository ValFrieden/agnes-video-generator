import cv2
import os

FRAMES_DIR = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"
img_s04 = cv2.imread(os.path.join(FRAMES_DIR, "anime_s04_qa_50.jpg"))
img_s03 = cv2.imread(os.path.join(FRAMES_DIR, "anime_s03_qa_50.jpg"))

# Let's save a test grid with coordinate marks on s04
s04_marked = img_s04.copy()
for x in range(0, 1280, 100):
    cv2.line(s04_marked, (x, 0), (x, 720), (255, 0, 0), 1)
    cv2.putText(s04_marked, str(x), (x+5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
for y in range(0, 720, 100):
    cv2.line(s04_marked, (0, y), (1280, y), (255, 0, 0), 1)
    cv2.putText(s04_marked, str(y), (10, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

cv2.imwrite(os.path.join(FRAMES_DIR, "s04_marked_grid.jpg"), s04_marked)

# Same for s03
s03_marked = img_s03.copy()
for x in range(0, 1280, 100):
    cv2.line(s03_marked, (x, 0), (x, 720), (255, 0, 0), 1)
    cv2.putText(s03_marked, str(x), (x+5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
for y in range(0, 720, 100):
    cv2.line(s03_marked, (0, y), (1280, y), (255, 0, 0), 1)
    cv2.putText(s03_marked, str(y), (10, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

cv2.imwrite(os.path.join(FRAMES_DIR, "s03_marked_grid.jpg"), s03_marked)
print("Saved grid marks.")
