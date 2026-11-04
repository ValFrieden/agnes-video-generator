import cv2
import numpy as np
import os

FRAMES_DIR = r"d:\Projects\VideoGenerator\moy_mir_iz_snov_frames"
OUT_IMG = os.path.join(FRAMES_DIR, "face_drift_comparison_audit.jpg")

def crop_face(img, manual_box=None):
    if img is None:
        return np.zeros((260, 260, 3), dtype=np.uint8)
    if manual_box is not None:
        x, y, w, h = manual_box
        sub = img[max(0, y):min(img.shape[0], y+h), max(0, x):min(img.shape[1], x+w)]
        return cv2.resize(sub, (260, 260), interpolation=cv2.INTER_AREA)
    return cv2.resize(img, (260, 260), interpolation=cv2.INTER_AREA)

def get_video_frame(vid_name, sec=3.0):
    p = os.path.join(FRAMES_DIR, vid_name)
    if not os.path.exists(p):
        return None
    cap = cv2.VideoCapture(p)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * fps))
    ret, frame = cap.read()
    cap.release()
    return frame

ref_valeri = cv2.imread(os.path.join(FRAMES_DIR, "real_valeri_portrait.jpg"))
ref_elena = cv2.imread(os.path.join(FRAMES_DIR, "real_woman_portrait.jpg"))
sheet_valeri = cv2.imread(os.path.join(FRAMES_DIR, "anime_character_valeri.png"))
sheet_elena = cv2.imread(os.path.join(FRAMES_DIR, "anime_character_elena.png"))

frame_s01 = get_video_frame("anime_scene_01_clean_veo.mp4", 3.0)
if frame_s01 is None:
    frame_s01 = get_video_frame("anime_scene_01.mp4", 3.0)
frame_s02 = get_video_frame("anime_scene_02_clean.mp4", 3.0)
frame_s03 = get_video_frame("anime_scene_03_clean.mp4", 3.0)
frame_s04 = get_video_frame("anime_scene_04_clean.mp4", 3.0)
img_s05 = cv2.imread(os.path.join(FRAMES_DIR, "anime_scene_05.png"))

def add_label(img, title, subtitle="", color=(255, 255, 255)):
    h, w = img.shape[:2]
    header = np.zeros((64, w, 3), dtype=np.uint8)
    cv2.putText(header, title, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.60, color, 2)
    if subtitle:
        cv2.putText(header, subtitle, (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
    return np.vstack([header, img])

# Manual exact bounding boxes [x, y, w, h]
# Valeri:
b_valeri_ref = crop_face(ref_valeri)
b_valeri_sheet = crop_face(sheet_valeri, (10, 80, 340, 360))
# S01: Valeri is walking on right-center: x=700..880, y=160..340
b_valeri_s01 = crop_face(frame_s01, (680, 160, 200, 200))
# S02: Valeri standing by cafe window: x=510..630, y=420..540
b_valeri_s02 = crop_face(frame_s02, (510, 420, 140, 160))
# S03: Valeri on left: x=530..640, y=140..270
b_valeri_s03 = crop_face(frame_s03, (530, 140, 130, 150))
# S04: Valeri on left: x=400..500, y=140..260
b_valeri_s04 = crop_face(frame_s04, (400, 140, 110, 130))
# S05: Valeri on left: x=530..620, y=230..350
b_valeri_s05 = crop_face(img_s05, (520, 220, 120, 150))

row_v = np.hstack([
    add_label(b_valeri_ref, "1. Real Valeri", "Wedding Photo"),
    add_label(b_valeri_sheet, "2. Anime Sheet", "Turnaround Master"),
    add_label(b_valeri_s01, "Scene 01", "Promenade"),
    add_label(b_valeri_s02, "Scene 02", "Cafe Window"),
    add_label(b_valeri_s03, "Scene 03", "Boulevard Glance"),
    add_label(b_valeri_s04, "Scene 04 (LATEST)", "Face Drift!", (0, 100, 255)),
    add_label(b_valeri_s05, "Scene 05", "Window Keyframe")
])

# Elena:
b_elena_ref = crop_face(ref_elena)
b_elena_sheet = crop_face(sheet_elena, (700, 80, 220, 240))
blank = np.zeros((260, 260, 3), dtype=np.uint8)
# S03: Elena on right: x=650..760, y=180..310
b_elena_s03 = crop_face(frame_s03, (650, 180, 130, 150))
# S04: Elena on right: x=500..580, y=220..330
b_elena_s04 = crop_face(frame_s04, (500, 220, 100, 120))
# S05: Elena on right: x=590..680, y=290..410
b_elena_s05 = crop_face(img_s05, (590, 290, 110, 140))

row_e = np.hstack([
    add_label(b_elena_ref, "1. Real Elena", "Wedding Photo"),
    add_label(b_elena_sheet, "2. Anime Sheet", "Turnaround Master"),
    add_label(blank, "Scene 01", "(Not in scene)"),
    add_label(blank, "Scene 02", "(Not in scene)"),
    add_label(b_elena_s03, "Scene 03", "Boulevard Glance"),
    add_label(b_elena_s04, "Scene 04 (LATEST)", "Face Drift!", (0, 100, 255)),
    add_label(b_elena_s05, "Scene 05", "Window Keyframe")
])

full_audit = np.vstack([row_v, row_e])
cv2.imwrite(OUT_IMG, full_audit)
print("Saved comparison audit to:", OUT_IMG)
