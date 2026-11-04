import cv2
import insightface
from insightface.app import FaceAnalysis

# 1. Initialize detector
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=-1, det_size=(640, 640))

# 2. Initialize swapper
swapper_model_path = r'd:\Projects\VideoGenerator\tools\insightface_models\inswapper_128.onnx'
swapper = insightface.model_zoo.get_model(swapper_model_path, download=False)

# 3. Source faces
valeri_src_img = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg')
woman_src_img = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_woman_portrait.jpg')

valeri_faces = app.get(valeri_src_img)
woman_faces = app.get(woman_src_img)

if not valeri_faces:
    print("Could not detect Valeri source face!")
    exit(1)
if not woman_faces:
    print("Could not detect Woman source face!")
    exit(1)

valeri_face = sorted(valeri_faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
woman_face = sorted(woman_faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]

print("Source faces successfully extracted!")

# 4. Swap onto target: test_man_casual.png
target_man = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\test_man_casual.png')
target_faces = app.get(target_man)
if target_faces:
    res_man = swapper.get(target_man, target_faces[0], valeri_face, paste_back=True)
    cv2.imwrite(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\swapped_man_casual.png', res_man)
    print("Saved swapped_man_casual.png")

# 5. Swap onto target: test_woman_casual.png
target_woman = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\test_woman_casual.png')
target_faces_w = app.get(target_woman)
if target_faces_w:
    res_woman = swapper.get(target_woman, target_faces_w[0], woman_face, paste_back=True)
    cv2.imwrite(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\swapped_woman_casual.png', res_woman)
    print("Saved swapped_woman_casual.png")

# 6. Swap onto target: test_couple_casual.png (both people)
target_couple = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\test_couple_casual.png')
couple_faces = app.get(target_couple)
# Sort faces from left to right: man is on left, woman is on right
if len(couple_faces) >= 2:
    couple_faces = sorted(couple_faces, key=lambda x: x.bbox[0])
    # left face = man
    res_couple = swapper.get(target_couple, couple_faces[0], valeri_face, paste_back=True)
    # right face = woman
    # re-detect on swapped or use existing bbox
    couple_faces_step2 = app.get(res_couple)
    couple_faces_step2 = sorted(couple_faces_step2, key=lambda x: x.bbox[0])
    res_couple_final = swapper.get(res_couple, couple_faces_step2[1], woman_face, paste_back=True)
    cv2.imwrite(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\swapped_couple_casual.png', res_couple_final)
    print("Saved swapped_couple_casual.png")
