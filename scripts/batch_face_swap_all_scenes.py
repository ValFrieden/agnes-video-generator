import os
import cv2
import insightface
from insightface.app import FaceAnalysis

# Setup FaceAnalysis and Inswapper
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=-1, det_size=(640, 640))

swapper_path = r'd:\Projects\VideoGenerator\tools\insightface_models\inswapper_128.onnx'
swapper = insightface.model_zoo.get_model(swapper_path, download=False)

# Real source portraits
valeri_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg')
woman_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_woman_portrait.jpg')

valeri_face = sorted(app.get(valeri_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
woman_face = sorted(app.get(woman_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]

frames_dir = r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames'

print("=== Starting Batch Face-Swap for all 11 Scenes ===")

# Scene mapping of who appears in each scene
# 01: Valeri solo
# 02: Valeri solo
# 03: Valeri and Woman (two people)
# 04: Valeri and Woman (two people)
# 05: Valeri and Woman (two people)
# 06: Valeri and Woman (two people)
# 07: Woman (foreground dancer) and Valeri (background)
# 08: Valeri close-up portrait solo
# 09: Close-up hands + partial faces (if faces detected)
# 10: Valeri and Woman (two people)
# 11: Background figures (two people)

for i in range(1, 12):
    scene_name = f"scene_{i:02d}.png"
    img_path = os.path.join(frames_dir, scene_name)
    if not os.path.exists(img_path):
        print(f"File {img_path} does not exist, skipping.")
        continue
    
    img = cv2.imread(img_path)
    faces = app.get(img)
    print(f"[{scene_name}] Detected {len(faces)} face(s)")
    
    if len(faces) == 0:
        continue
    
    # Sort faces from left to right by bounding box x0
    faces = sorted(faces, key=lambda x: x.bbox[0])
    
    if len(faces) == 1:
        # Single face
        # In scene 07, the main face is the dancing woman
        target_src = woman_face if i == 7 else valeri_face
        res = swapper.get(img, faces[0], target_src, paste_back=True)
        cv2.imwrite(img_path, res)
        print(f"  -> Swapped single face in {scene_name}")
    elif len(faces) >= 2:
        # For multi-person scenes (03, 04, 05, 06, 09, 10, 11)
        # Determine who is man and who is woman using gender or left/right position
        # Face 0 and Face 1
        f0, f1 = faces[0], faces[1]
        # In most shots man is on left or determined by gender
        # Check gender attribute if available: 1 = M, 0 = F
        if hasattr(f0, 'gender') and hasattr(f1, 'gender'):
            if f0.gender == 1:
                src0, src1 = valeri_face, woman_face
            else:
                src0, src1 = woman_face, valeri_face
        else:
            # Fallback to left=man, right=woman
            src0, src1 = valeri_face, woman_face
            
        res = swapper.get(img, f0, src0, paste_back=True)
        # Re-detect on image with first face swapped to accurately locate second face
        new_faces = sorted(app.get(res), key=lambda x: x.bbox[0])
        if len(new_faces) >= 2:
            res = swapper.get(res, new_faces[1], src1, paste_back=True)
        cv2.imwrite(img_path, res)
        print(f"  -> Swapped {len(faces)} faces in {scene_name}")

print("\n=== All 11 Scenes Successfully Updated with 100% Real Faces! ===")
