import asyncio
import json
import urllib.request
import websockets
import base64
import time
import os
import shutil
import cv2
import insightface

OUT_DIR = os.path.abspath("moy_mir_iz_snov_frames")
RAW_VIDEO = os.path.join(OUT_DIR, "scene_02_fresh_raw.mp4")
FINAL_VIDEO = os.path.join(OUT_DIR, "scene_02_final_valeri.mp4")
ART_DIR = r"C:\Users\Valeri\.gemini\antigravity-ide\brain\556e46de-ed40-412d-a023-3012577769a7"
os.makedirs(ART_DIR, exist_ok=True)

def get_ws_url():
    req = urllib.request.urlopen("http://localhost:9222/json")
    pages = json.loads(req.read().decode())
    flow = next(p for p in pages if "flow.google.com" in p.get("url", ""))
    return flow["webSocketDebuggerUrl"]

async def monitor_and_download():
    ws_url = get_ws_url()
    print(f"Connecting to Flow CDP: {ws_url}", flush=True)
    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        # 1. Monitor progress percentage
        print("Monitoring Veo 3.1 generation progress for Scene 02...", flush=True)
        for step in range(120): # up to 10 minutes
            eval_pct = """(() => {
                const textElements = Array.from(document.querySelectorAll('span, div, p, flow-video-tile')).map(e => (e.innerText || '').trim());
                const pctMatch = textElements.find(t => /^\\d+\\s*%$/.test(t));
                const spinners = document.querySelectorAll('mat-spinner, mat-progress-spinner, [role="progressbar"], .loading');
                const tiles = document.querySelectorAll('flow-video-tile, [class*="video-tile"]');
                return {
                    pct: pctMatch || null,
                    hasSpinner: spinners.length > 0,
                    tilesCount: tiles.length
                };
            })()"""
            await ws.send(json.dumps({'id': 100 + step, 'method': 'Runtime.evaluate', 'params': {'expression': eval_pct, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            pct = val.get('pct')
            tiles = val.get('tilesCount', 0)
            print(f"[{time.strftime('%H:%M:%S')}] Progress: {pct or 'Generating...'} | Tiles on canvas: {tiles}", flush=True)

            # We know Scene 01 created tile 1, so Scene 02 creates tile 2
            if tiles >= 2 and not val.get('hasSpinner') and step > 4:
                print("Generation complete! Found new video tile for Scene 02.", flush=True)
                break
            elif not val.get('hasSpinner') and not pct and step > 10 and tiles >= 1:
                # In case canvas replaced or updated
                print("Spinners gone, checking if video tile is ready...", flush=True)
                break
            await asyncio.sleep(5)

        await asyncio.sleep(3)

        # 2. Select the newest video tile (top-left tile)
        print("Clicking top video tile...", flush=True)
        click_tile = """(() => {
            const tiles = Array.from(document.querySelectorAll('flow-video-tile, [class*="video-tile"]'));
            if (tiles.length > 0) {
                tiles[0].click();
                return 'Clicked video tile';
            }
            return 'No video tiles';
        })()"""
        await ws.send(json.dumps({'id': 200, 'method': 'Runtime.evaluate', 'params': {'expression': click_tile, 'returnByValue': True}}))
        print(json.loads(await ws.recv())['result']['result']['value'], flush=True)
        await asyncio.sleep(2)

        # 3. Install Blob Hook for instant download capture
        hook_script = """(() => {
            window.__captured_blobs = [];
            const origCreate = URL.createObjectURL;
            URL.createObjectURL = function(obj) {
                const url = origCreate.call(URL, obj);
                if (obj instanceof Blob) {
                    const reader = new FileReader();
                    reader.onload = () => {
                        window.__captured_blobs.push({
                            url: url, size: obj.size, type: obj.type, data: reader.result
                        });
                    };
                    reader.readAsDataURL(obj);
                }
                return url;
            };
            return true;
        })()"""
        await ws.send(json.dumps({'id': 205, 'method': 'Runtime.evaluate', 'params': {'expression': hook_script, 'returnByValue': True}}))
        await ws.recv()

        # 4. Open download menu
        open_menu = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen') || (b.innerText || '').toLowerCase().includes('download'));
            if (dl) { dl.click(); return true; }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 210, 'method': 'Runtime.evaluate', 'params': {'expression': open_menu, 'returnByValue': True}}))
        print("Opened download menu:", json.loads(await ws.recv())['result']['result']['value'], flush=True)
        await asyncio.sleep(1)

        # 5. Click 720p option
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
                print(f"SUCCESS! Scene 02 raw video downloaded: {len(video_bytes)} bytes -> {RAW_VIDEO}", flush=True)
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

def run_face_swap_pipeline():
    print("\n=== STARTING INSIGHTFACE FACE SWAP (inswapper_128) FOR SCENE 02 ===", flush=True)
    app = insightface.app.FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=-1, det_size=(640, 640))

    swapper_path = r'd:\Projects\VideoGenerator\tools\insightface_models\inswapper_128.onnx'
    swapper = insightface.model_zoo.get_model(swapper_path, download=False)

    valeri_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg')
    valeri_face = sorted(app.get(valeri_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
    print("Valeri wedding portrait face vector ready!", flush=True)

    cap = cv2.VideoCapture(RAW_VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Processing Scene 02 video: {w}x{h} @ {fps} fps, {total_frames} frames", flush=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(FINAL_VIDEO, fourcc, fps, (w, h))

    idx_25 = int(total_frames * 0.25)
    idx_50 = int(total_frames * 0.50)
    idx_75 = int(total_frames * 0.75)
    qa_map = {idx_25: 'qa_s02_25.jpg', idx_50: 'qa_s02_50.jpg', idx_75: 'qa_s02_75.jpg'}

    count = 0
    swapped = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        faces = app.get(frame)
        if len(faces) > 0:
            main_f = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
            frame = swapper.get(frame, main_f, valeri_face, paste_back=True)
            swapped += 1
        out.write(frame)

        if count in qa_map:
            name = qa_map[count]
            p_local = os.path.join(OUT_DIR, name)
            p_art = os.path.join(ART_DIR, name)
            cv2.imwrite(p_local, frame)
            shutil.copy2(p_local, p_art)
            print(f"Saved QA checkpoint: {name}", flush=True)

        count += 1

    cap.release()
    out.release()
    print(f"\nSCENE 02 COMPLETED SUCCESSFULLY! {count} frames processed ({swapped} faces swapped).", flush=True)
    print(f"Final video: {FINAL_VIDEO}", flush=True)

if __name__ == '__main__':
    ok = asyncio.run(monitor_and_download())
    if ok and os.path.exists(RAW_VIDEO):
        run_face_swap_pipeline()
    else:
        print("Failed to download raw video for Scene 02.")
