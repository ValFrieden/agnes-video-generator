import os
import shutil
import cv2
import numpy as np
import insightface

RAW_VIDEO = r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\scene_04_fresh_raw.mp4'
FINAL_VIDEO = r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\scene_04_final_valeri.mp4'
OUT_DIR = r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames'
ART_DIR = r'C:\Users\Valeri\.gemini\antigravity-ide\brain\556e46de-ed40-412d-a023-3012577769a7'

def main():
    print("=== STARTING INSIGHTFACE DUAL FACE SWAP FOR SCENE 04 ===", flush=True)
    app = insightface.app.FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=-1, det_size=(640, 640))

    swapper_path = r'd:\Projects\VideoGenerator\tools\insightface_models\inswapper_128.onnx'
    swapper = insightface.model_zoo.get_model(swapper_path, download=False)

    valeri_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg')
    woman_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_woman_portrait.jpg')

    valeri_face = sorted(app.get(valeri_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
    woman_face = sorted(app.get(woman_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
    print("Valeri & Elena wedding reference face vectors ready!", flush=True)

    cap = cv2.VideoCapture(RAW_VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Processing Scene 04 video: {w}x{h} @ {fps} fps, {total_frames} frames", flush=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(FINAL_VIDEO, fourcc, fps, (w, h))

    idx_25 = int(total_frames * 0.25)
    idx_50 = int(total_frames * 0.50)
    idx_75 = int(total_frames * 0.75)
    qa_map = {idx_25: 'qa_s04_25.jpg', idx_50: 'qa_s04_50.jpg', idx_75: 'qa_s04_75.jpg'}

    count = 0
    valeri_count = 0
    elena_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = app.get(frame)
        if len(faces) > 0:
            for f in faces:
                sim_v = float(np.dot(f.normed_embedding, valeri_face.normed_embedding))
                sim_w = float(np.dot(f.normed_embedding, woman_face.normed_embedding))

                if sim_v > sim_w:
                    frame = swapper.get(frame, f, valeri_face, paste_back=True)
                    valeri_count += 1
                else:
                    frame = swapper.get(frame, f, woman_face, paste_back=True)
                    elena_count += 1

        out.write(frame)

        if count in qa_map:
            name = qa_map[count]
            p_local = os.path.join(OUT_DIR, name)
            p_art = os.path.join(ART_DIR, name)
            cv2.imwrite(p_local, frame)
            shutil.copy2(p_local, p_art)
            print(f"Saved QA checkpoint: {name} (frame {count})", flush=True)

        count += 1
        if count % 30 == 0:
            print(f"Processed {count}/{total_frames} frames...", flush=True)

    cap.release()
    out.release()

    # Copy final video to artifact folder as well
    p_art_vid = os.path.join(ART_DIR, 'scene_04_final_valeri.mp4')
    shutil.copy2(FINAL_VIDEO, p_art_vid)

    print(f"\nSCENE 04 COMPLETED! Total frames: {count} (Valeri swaps: {valeri_count}, Elena swaps: {elena_count})", flush=True)
    print(f"Final video: {FINAL_VIDEO}", flush=True)

if __name__ == '__main__':
    main()
