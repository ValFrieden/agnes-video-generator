import json, asyncio, websockets, urllib.request, os, time, subprocess

OUT_DIR = os.path.abspath('d:/Projects/VideoGenerator/kuda_idu_frames/clips')
FINAL_CLIP = os.path.join(OUT_DIR, 'clip_02.mp4')
DOWNLOADS_DIR = os.path.abspath('C:/Users/Valeri/Downloads')

req = urllib.request.Request('http://127.0.0.1:9222/json/list')
with urllib.request.urlopen(req, timeout=3) as resp:
    tabs = json.loads(resp.read().decode('utf-8'))
ws_url = [t['webSocketDebuggerUrl'] for t in tabs if 'flow.google.com' in t.get('url', '')][0]

async def trigger_download():
    before_files = set(os.listdir(DOWNLOADS_DIR))

    async with websockets.connect(ws_url) as ws:
        # Click the LAST Herunterladen button
        click_dl = """(() => {
            const btns = Array.from(document.querySelectorAll('[aria-label*="Herunterladen"], [aria-label*="Download"]'));
            if (btns.length > 0) {
                const target = btns[btns.length - 1];
                target.click();
                return { clicked: true, count: btns.length };
            }
            return { clicked: false };
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_dl, 'returnByValue': True}}))
        raw1 = await ws.recv()
        print('Click last DL button res:', json.loads(raw1)['result']['result']['value'])

        await asyncio.sleep(1)

        # Click the 720p menu item
        click_720 = """(() => {
            const items = Array.from(document.querySelectorAll('[role="menuitem"], mat-option, .mat-mdc-menu-item, button'));
            const item720 = items.find(i => i.innerText && i.innerText.includes('720p'));
            if (item720) {
                item720.click();
                return { clicked: true, text: item720.innerText.trim() };
            }
            return { clicked: false };
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': click_720, 'returnByValue': True}}))
        raw2 = await ws.recv()
        print('Click 720p res:', json.loads(raw2)['result']['result']['value'])

    # Wait for new download in Downloads folder
    print('Waiting for download to appear in Downloads folder...')
    for _ in range(30):
        await asyncio.sleep(1)
        current_files = set(os.listdir(DOWNLOADS_DIR))
        new_files = [f for f in (current_files - before_files) if not f.endswith('.crdownload') and not f.endswith('.tmp')]
        if new_files:
            downloaded = os.path.join(DOWNLOADS_DIR, new_files[0])
            print(f'Downloaded file: {downloaded} ({os.path.getsize(downloaded)} bytes)')
            if os.path.exists(FINAL_CLIP):
                os.remove(FINAL_CLIP)
            os.rename(downloaded, FINAL_CLIP)
            print(f'Renamed to: {FINAL_CLIP}')
            break

    # Extract QA keyframes
    if os.path.exists(FINAL_CLIP) and os.path.getsize(FINAL_CLIP) > 10000:
        print('Extracting QA verification frames for Scene 02 (25%, 50%, 75%)...')
        try:
            dur_out = subprocess.check_output(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{FINAL_CLIP}"', shell=True, text=True).strip()
            dur = float(dur_out) if dur_out else 8.0
            print(f'Scene 02 duration: {dur}s')
            qa_files = []
            for pct in [25, 50, 75]:
                t = round(dur * (pct / 100.0), 2)
                qa_file = os.path.join(OUT_DIR, f'clip_02_qa{pct}.png')
                subprocess.run(f'ffmpeg -y -ss {t} -i "{FINAL_CLIP}" -frames:v 1 "{qa_file}"', shell=True, capture_output=True)
                qa_files.append(qa_file)
                print(f'QA {pct}% frame saved: {qa_file}')

            trio_file = os.path.join(OUT_DIR, 'clip_02_qa_trio.png')
            subprocess.run(f'ffmpeg -y -i "{qa_files[0]}" -i "{qa_files[1]}" -i "{qa_files[2]}" -filter_complex "[0:v][1:v][2:v]hstack=inputs=3[v]" -map "[v]" "{trio_file}"', shell=True, capture_output=True)
            print(f'Scene 02 QA contact sheet saved: {trio_file}')
        except Exception as e:
            print(f'QA extraction error: {e}')

asyncio.run(trigger_download())
