import asyncio
import json
import base64
import os
import time
import shutil
import urllib.request
import websockets
import cv2
import numpy as np
import insightface

RAW_VIDEO = r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\scene_03_fresh_raw.mp4'
FINAL_VIDEO = r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\scene_03_final_valeri.mp4'
OUT_DIR = r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames'
ART_DIR = r'C:\Users\Valeri\.gemini\antigravity-ide\brain\556e46de-ed40-412d-a023-3012577769a7'

async def monitor_and_download():
    # 1. Discover Flow CDP tab
    req = urllib.request.urlopen('http://localhost:9222/json')
    tabs = json.loads(req.read().decode())
    flow_tab = next(t for t in tabs if 'flow.google.com' in t.get('url', ''))
    ws_url = flow_tab['webSocketDebuggerUrl']
    print(f"Connecting to Flow CDP: {ws_url}", flush=True)

    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        # Enable Runtime
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
        await ws.recv()

        # 2. Inject blob capture hook immediately
        hook_script = """(() => {
            window.__captured_blobs = [];
            const orig = URL.createObjectURL;
            URL.createObjectURL = function(obj) {
                const url = orig.apply(this, arguments);
                if (obj && obj.type && obj.type.includes('video')) {
                    const reader = new FileReader();
                    reader.onload = function() {
                        window.__captured_blobs.push({ url: url, data: reader.result, size: obj.size, type: obj.type });
                    };
                    reader.readAsDataURL(obj);
                }
                return url;
            };
            return true;
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': hook_script}}))
        await ws.recv()

        # 3. Monitor video generation progress
        print("Monitoring Veo 3.1 generation progress for Scene 03...", flush=True)
        gen_started = False
        start_time = time.time()
        
        while time.time() - start_time < 300:
            await asyncio.sleep(4)
            check_script = """(() => {
                const text = document.body.innerText || '';
                const progressMatch = text.match(/(\\d+)\\s*%/);
                const isGenerating = text.includes('Generierung') || text.includes('Generating') || !!progressMatch;
                const tiles = document.querySelectorAll('video, flow-asset-tile, [data-tile-id], .asset-tile');
                return {
                    generating: isGenerating,
                    progress: progressMatch ? progressMatch[1] + '%' : (isGenerating ? 'Generating...' : 'Idle'),
                    tilesCount: tiles.length
                };
            })()"""
            await ws.send(json.dumps({'id': 100, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
            resp = json.loads(await ws.recv())
            val = resp.get('result', {}).get('result', {}).get('value', {})
            prog = val.get('progress', 'Unknown')
            t_count = val.get('tilesCount', 0)
            is_gen = val.get('generating', False)

            print(f"[{time.strftime('%H:%M:%S')}] Progress: {prog} | Tiles on canvas: {t_count}", flush=True)

            if is_gen:
                gen_started = True

            # If generation was started and now idle, or after 25s if prog is Idle
            if gen_started and not is_gen:
                print("Generation complete! Found new video tile for Scene 03.", flush=True)
                break
            if time.time() - start_time > 20 and not is_gen and not gen_started:
                # Generation might have already finished quickly or didn't show progress text
                print("Checking if generation already complete...", flush=True)
                break

        await asyncio.sleep(3)

        # 4. Click top video tile on canvas
        print("Clicking top video tile...", flush=True)
        click_tile = """(() => {
            const vids = Array.from(document.querySelectorAll('video'));
            for (const v of vids) {
                const rect = v.getBoundingClientRect();
                if (rect.width > 120 && rect.height > 80 && rect.top > 50) {
                    v.closest('[data-tile-id], flow-asset-tile, div') || v;
                    v.click();
                    return true;
                }
            }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 200, 'method': 'Runtime.evaluate', 'params': {'expression': click_tile, 'returnByValue': True}}))
        await ws.recv()
        print("Clicked video tile", flush=True)
        await asyncio.sleep(2)

        # 5. Click download icon / open download menu
        click_dl = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const dlBtn = btns.find(b => (b.innerText || '').includes('download') || b.querySelector('i:has-text("download"), .mat-icon:has-text("download")') || (b.getAttribute('aria-label') || '').includes('Herunterladen') || (b.getAttribute('aria-label') || '').includes('Download'));
            if (dlBtn) { dlBtn.click(); return true; }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 210, 'method': 'Runtime.evaluate', 'params': {'expression': click_dl, 'returnByValue': True}}))
        menu_opened = json.loads(await ws.recv())['result']['result']['value']
        print("Opened download menu:", menu_opened, flush=True)
        await asyncio.sleep(1.5)

        # Click "720p" option
        click_720 = """(() => {
            const btns = Array.from(document.querySelectorAll('button.mat-mdc-menu-item, flow-menu-item button, [role="menuitem"], button'));
            const target = btns.find(b => (b.innerText || '').includes('720p'));
            if (target) { target.click(); return true; }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 220, 'method': 'Runtime.evaluate', 'params': {'expression': click_720, 'returnByValue': True}}))
        print("Clicked 720p:", json.loads(await ws.recv())['result']['result']['value'], flush=True)

        # 6. Extract captured blob data
        saved = False
        print("Waiting for video blob capture...", flush=True)
        for i in range(30):
            await asyncio.sleep(1)
            check_script = "window.__captured_blobs && window.__captured_blobs.length > 0 && !!window.__captured_blobs[0].data"
            await ws.send(json.dumps({'id': 300 + i, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
            c_resp = await ws.recv()
            has_blob = json.loads(c_resp).get('result', {}).get('result', {}).get('value', False)
            if has_blob:
                extract_script = "window.__captured_blobs[0].data"
                await ws.send(json.dumps({'id': 999, 'method': 'Runtime.evaluate', 'params': {'expression': extract_script, 'returnByValue': True}}))
                ext_resp = await ws.recv()
                data_url = json.loads(ext_resp)['result']['result']['value']
                header, b64data = data_url.split(',', 1)
                video_bytes = base64.b64decode(b64data)
                with open(RAW_VIDEO, 'wb') as f:
                    f.write(video_bytes)
                print(f"SUCCESS! Scene 03 raw video downloaded: {len(video_bytes)} bytes -> {RAW_VIDEO}", flush=True)
                saved = True
                break

        # Fallback check ~/Downloads if blob hook didn't catch
        if not saved:
            dl_user = os.path.expanduser('~/Downloads')
            for i in range(15):
                await asyncio.sleep(1)
                dl_files = [os.path.join(dl_user, f) for f in os.listdir(dl_user) if f.endswith('.mp4')]
                recent = [f for f in dl_files if time.time() - os.path.getmtime(f) < 45]
                if recent:
                    shutil.copy2(recent[0], RAW_VIDEO)
                    print(f"Found in ~/Downloads, copied to {RAW_VIDEO}", flush=True)
                    saved = True
                    break

        return saved

def run_dual_face_swap_pipeline():
    print("\n=== STARTING INSIGHTFACE DUAL FACE SWAP (inswapper_128) FOR SCENE 03 ===", flush=True)
    app = insightface.app.FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=-1, det_size=(640, 640))

    swapper_path = r'd:\Projects\VideoGenerator\tools\insightface_models\inswapper_128.onnx'
    swapper = insightface.model_zoo.get_model(swapper_path, download=False)

    valeri_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg')
    woman_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_woman_portrait.jpg')

    valeri_face = sorted(app.get(valeri_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
    woman_face = sorted(app.get(woman_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
    print("Valeri and Elena wedding reference face vectors ready!", flush=True)

    cap = cv2.VideoCapture(RAW_VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Processing Scene 03 video: {w}x{h} @ {fps} fps, {total_frames} frames", flush=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(FINAL_VIDEO, fourcc, fps, (w, h))

    idx_25 = int(total_frames * 0.25)
    idx_50 = int(total_frames * 0.50)
    idx_75 = int(total_frames * 0.75)
    qa_map = {idx_25: 'qa_s03_25.jpg', idx_50: 'qa_s03_50.jpg', idx_75: 'qa_s03_75.jpg'}

    count = 0
    swapped_valeri = 0
    swapped_elena = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        faces = app.get(frame)
        if len(faces) > 0:
            # Sort faces by size (largest first)
            for f in faces:
                sim_v = float(np.dot(f.normed_embedding, valeri_face.normed_embedding))
                sim_w = float(np.dot(f.normed_embedding, woman_face.normed_embedding))
                
                # Check similarity and gender cues
                if sim_v > sim_w and (sim_v > 0.35 or f.gender == 1):
                    frame = swapper.get(frame, f, valeri_face, paste_back=True)
                    swapped_valeri += 1
                elif sim_w > sim_v and (sim_w > 0.35 or f.gender == 0):
                    frame = swapper.get(frame, f, woman_face, paste_back=True)
                    swapped_elena += 1

        out.write(frame)

        if count in qa_map:
            name = qa_map[count]
            p_local = os.path.join(OUT_DIR, name)
            p_art = os.path.join(ART_DIR, name)
            cv2.imwrite(p_local, frame)
            shutil.copy2(p_local, p_art)
            print(f"Saved QA checkpoint: {name} (frame {count})", flush=True)

        count += 1

    cap.release()
    out.release()
    print(f"\nSCENE 03 COMPLETED SUCCESSFULLY! {count} frames processed (Valeri swaps: {swapped_valeri}, Elena swaps: {swapped_elena}).", flush=True)
    print(f"Final video: {FINAL_VIDEO}", flush=True)

if __name__ == '__main__':
    ok = asyncio.run(monitor_and_download())
    if ok and os.path.exists(RAW_VIDEO):
        run_dual_face_swap_pipeline()
    else:
        print("Failed to download raw video for Scene 03.")
