import cv2
import os
import insightface
import shutil

def process_scene01():
    in_video = "moy_mir_iz_snov_frames/scene_01_valeri_i2v_raw.mp4"
    out_video = "moy_mir_iz_snov_frames/scene_01_final_valeri.mp4"
    qa_dir = "moy_mir_iz_snov_frames"
    art_dir = r"C:\Users\Valeri\.gemini\antigravity-ide\brain\58068fde-29f2-49e3-b0ff-d80b59861e7b"
    os.makedirs(art_dir, exist_ok=True)

    print("Initializing InsightFace buffalo_l...", flush=True)
    app = insightface.app.FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=-1, det_size=(640, 640))

    swapper_path = r'd:\Projects\VideoGenerator\tools\insightface_models\inswapper_128.onnx'
    swapper = insightface.model_zoo.get_model(swapper_path, download=False)

    valeri_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg')
    valeri_faces = app.get(valeri_src)
    valeri_face = sorted(valeri_faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
    print("Valeri source face vector loaded!", flush=True)

    cap = cv2.VideoCapture(in_video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video input: {w}x{h} @ {fps} fps, total frames: {total_frames}", flush=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_video, fourcc, fps, (w, h))

    idx_25 = int(total_frames * 0.25)
    idx_50 = int(total_frames * 0.50)
    idx_75 = int(total_frames * 0.75)
    qa_indices = {idx_25: 'qa_clean_s01_25.jpg', idx_50: 'qa_clean_s01_50.jpg', idx_75: 'qa_clean_s01_75.jpg'}

    count = 0
    swapped_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        faces = app.get(frame)
        if len(faces) > 0:
            main_face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
            frame = swapper.get(frame, main_face, valeri_face, paste_back=True)
            swapped_count += 1
        
        out.write(frame)

        if count in qa_indices:
            name = qa_indices[count]
            p_local = os.path.join(qa_dir, name)
            p_art = os.path.join(art_dir, name)
            cv2.imwrite(p_local, frame)
            shutil.copy2(p_local, p_art)
            print(f"Saved QA checkpoint frame at frame {count}: {name}", flush=True)

        count += 1

    cap.release()
    out.release()
    print(f"COMPLETE! Processed {count} frames ({swapped_count} swapped). Saved to {out_video}", flush=True)

if __name__ == '__main__':
    process_scene01()
