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

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

OUT_DIR = os.path.abspath("moy_mir_iz_snov_frames")
RAW_VIDEO = os.path.join(OUT_DIR, "scene_01_valeri_i2v_raw.mp4")
FINAL_VIDEO = os.path.join(OUT_DIR, "scene_01_final_valeri.mp4")
ART_DIR = r"C:\Users\Valeri\.gemini\antigravity-ide\brain\58068fde-29f2-49e3-b0ff-d80b59861e7b"

async def monitor_and_download():
    ws_url = get_ws_url()
    print("Connecting to Flow to monitor Image-to-Video generation...", flush=True)
    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        # 1. Monitor percentage
        for step in range(120): # up to 600s
            eval_pct = """(() => {
                const textElements = Array.from(document.querySelectorAll('span, div, p, flow-video-tile')).map(e => (e.innerText || '').trim());
                const pctMatch = textElements.find(t => /^\\d+\\s*%$/.test(t));
                const spinners = document.querySelectorAll('mat-spinner, mat-progress-spinner, [role="progressbar"]');
                return {
                    pct: pctMatch || null,
                    hasSpinner: spinners.length > 0
                };
            })()"""
            await ws.send(json.dumps({'id': 100 + step, 'method': 'Runtime.evaluate', 'params': {'expression': eval_pct, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            pct = val.get('pct')
            print(f"[{time.strftime('%H:%M:%S')}] i2v Progress: {pct or 'Finalizing / Ready'}", flush=True)

            if not pct and not val.get('hasSpinner') and step > 3:
                print("i2v Generation finished!", flush=True)
                break
            await asyncio.sleep(5)

        await asyncio.sleep(3)

        # 2. Click the new video tile (top-left tile in grid)
        print("Selecting new video tile...", flush=True)
        click_tile = """(() => {
            const tiles = Array.from(document.querySelectorAll('flow-video-tile, [class*="video-tile"]'));
            if (tiles.length > 0) {
                tiles[0].click();
                return 'Clicked top video tile';
            }
            return 'No video tiles';
        })()"""
        await ws.send(json.dumps({'id': 200, 'method': 'Runtime.evaluate', 'params': {'expression': click_tile, 'returnByValue': True}}))
        print(json.loads(await ws.recv())['result']['result']['value'], flush=True)
        await asyncio.sleep(2)

        # 3. Open download menu
        open_menu = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen') || (b.innerText || '').toLowerCase().includes('download'));
            if (dl) { dl.click(); return true; }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 210, 'method': 'Runtime.evaluate', 'params': {'expression': open_menu, 'returnByValue': True}}))
        print("Opened download menu:", json.loads(await ws.recv())['result']['result']['value'], flush=True)
        await asyncio.sleep(1)

        # 4. Find 720p coords and click with real mouse event
        find_720 = """(() => {
            const els = Array.from(document.querySelectorAll('.mat-mdc-menu-panel *, [role="menu"] *, [role="menuitem"], button, div'));
            const targets = els.filter(e => (e.innerText || '').trim().includes('720p'));
            let best = null;
            let minArea = 1e9;
            for (const t of targets) {
                const r = t.getBoundingClientRect();
                const area = r.width * r.height;
                if (area > 10 && area < minArea) {
                    minArea = area;
                    best = { x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, h: r.height };
                }
            }
            return best;
        })()"""
        await ws.send(json.dumps({'id': 220, 'method': 'Runtime.evaluate', 'params': {'expression': find_720, 'returnByValue': True}}))
        coords = json.loads(await ws.recv())['result']['result']['value']
        print("720p button coords:", coords, flush=True)

        if coords:
            cx, cy = coords['x'], coords['y']
            await ws.send(json.dumps({'id': 230, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await asyncio.sleep(0.1)
            await ws.send(json.dumps({'id': 231, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Clicked 720p download!", flush=True)

        # 5. Wait for downloaded file in ~/Downloads
        dl_user = os.path.expanduser('~/Downloads')
        print("Monitoring ~/Downloads for new MP4 file...", flush=True)
        saved = False
        for i in range(30):
            await asyncio.sleep(1)
            dl_files = [os.path.join(dl_user, f) for f in os.listdir(dl_user) if f.endswith('.mp4')]
            recent = [f for f in dl_files if time.time() - os.path.getmtime(f) < 45]
            if recent:
                src_file = recent[0]
                print(f"Downloaded file detected: {src_file} ({os.path.getsize(src_file)} bytes)", flush=True)
                shutil.copy2(src_file, RAW_VIDEO)
                print(f"Copied to {RAW_VIDEO}", flush=True)
                saved = True
                break

        return saved

def run_face_swap_pipeline():
    print("\n=== STARTING FRAME-BY-FRAME FACE SWAP (InsightFace inswapper_128) ===", flush=True)
    app = insightface.app.FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=-1, det_size=(640, 640))

    swapper_path = r'd:\Projects\VideoGenerator\tools\insightface_models\inswapper_128.onnx'
    swapper = insightface.model_zoo.get_model(swapper_path, download=False)

    valeri_src = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\real_valeri_portrait.jpg')
    valeri_face = sorted(app.get(valeri_src), key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
    print("Valeri wedding face vector ready!", flush=True)

    cap = cv2.VideoCapture(RAW_VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Processing video: {w}x{h} @ {fps} fps, {total_frames} frames", flush=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(FINAL_VIDEO, fourcc, fps, (w, h))

    idx_25 = int(total_frames * 0.25)
    idx_50 = int(total_frames * 0.50)
    idx_75 = int(total_frames * 0.75)
    qa_map = {idx_25: 'qa_valeri_s01_25.jpg', idx_50: 'qa_valeri_s01_50.jpg', idx_75: 'qa_valeri_s01_75.jpg'}

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
            print(f"Saved checkpoint frame: {name}", flush=True)

        count += 1

    cap.release()
    out.release()
    print(f"SUCCESS! {count} frames processed ({swapped} face-swapped). Video: {FINAL_VIDEO}", flush=True)

if __name__ == '__main__':
    ok = asyncio.run(monitor_and_download())
    if ok and os.path.exists(RAW_VIDEO):
        run_face_swap_pipeline()
    else:
        print("Could not download raw video file.")
