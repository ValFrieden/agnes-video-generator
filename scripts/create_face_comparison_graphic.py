import cv2
import numpy as np
import os

FRAMES_DIR = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"
OUT_IMG = os.path.join(FRAMES_DIR, "faces_comparison_s03_vs_s04_vs_canon.jpg")

real_valeri = cv2.imread(os.path.join(FRAMES_DIR, "real_valeri_portrait.jpg"))
real_elena = cv2.imread(os.path.join(FRAMES_DIR, "real_woman_portrait.jpg"))
sheet_valeri = cv2.imread(os.path.join(FRAMES_DIR, "anime_character_valeri.png"))
sheet_elena = cv2.imread(os.path.join(FRAMES_DIR, "anime_character_elena.png"))

v_s03 = cv2.imread(os.path.join(FRAMES_DIR, "crop_v_s03.jpg"))
v_s04 = cv2.imread(os.path.join(FRAMES_DIR, "crop_v_s04.jpg"))
e_s03 = cv2.imread(os.path.join(FRAMES_DIR, "crop_e_s03.jpg"))
e_s04 = cv2.imread(os.path.join(FRAMES_DIR, "crop_e_s04.jpg"))

def fit_card(img, target_size=(320, 320)):
    if img is None:
        return np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
    h, w = img.shape[:2]
    scale = min(target_size[0]/w, target_size[1]/h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
    y_off = (target_size[1] - nh) // 2
    x_off = (target_size[0] - nw) // 2
    canvas[y_off:y_off+nh, x_off:x_off+nw] = resized
    return canvas

def create_card(img, title, subtitle="", border_color=None):
    base = fit_card(img, (320, 320))
    header = np.zeros((70, 320, 3), dtype=np.uint8)
    title_color = (0, 230, 255) if border_color else (255, 255, 255)
    cv2.putText(header, title, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.60, title_color, 2)
    if subtitle:
        cv2.putText(header, subtitle, (10, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
    card = np.vstack([header, base])
    if border_color:
        cv2.rectangle(card, (0, 0), (card.shape[1]-1, card.shape[0]-1), border_color, 3)
    return card

# Valeri Row
v_real_card = create_card(real_valeri, "1. Real Valeri", "Hochzeit/DSC_9860")
v_sheet_card = create_card(sheet_valeri[20:350, 20:350], "2. Anime Sheet", "Turnaround Approved")
v_s03_card = create_card(v_s03, "3. Scene 03 Video", "MATCH: Stubble & Jawline", (0, 200, 0))
v_s04_card = create_card(v_s04, "4. Scene 04 Video", "DRIFT: Lost stubble/boy face!", (0, 0, 255))
row_valeri = np.hstack([v_real_card, v_sheet_card, v_s03_card, v_s04_card])

# Elena Row
e_real_card = create_card(real_elena, "1. Real Elena", "Hochzeit/DSC_9317")
e_sheet_card = create_card(sheet_elena[50:350, 660:960], "2. Anime Sheet", "Turnaround Approved")
e_s03_card = create_card(e_s03, "3. Scene 03 Video", "MATCH: Profile & Proportions", (0, 200, 0))
e_s04_card = create_card(e_s04, "4. Scene 04 Video", "DRIFT: Generic anime girl!", (0, 0, 255))
row_elena = np.hstack([e_real_card, e_sheet_card, e_s03_card, e_s04_card])

banner = np.zeros((80, row_valeri.shape[1], 3), dtype=np.uint8)
cv2.putText(banner, "FACIAL CONSISTENCY & DRIFT AUDIT: SCENE 03 vs SCENE 04 (LATEST)", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2)

full_img = np.vstack([banner, row_valeri, row_elena])
cv2.imwrite(OUT_IMG, full_img)
print("Saved perfect comparison to:", OUT_IMG)
