import json, asyncio, websockets, urllib.request, time, os, subprocess

OUT_VIDEO = os.path.abspath('d:/Projects/VideoGenerator/kuda_idu_frames/clips/clip_01.mp4')

def get_flow_ws():
    req = urllib.request.Request('http://127.0.0.1:9222/json/list')
    with urllib.request.urlopen(req, timeout=3) as resp:
        tabs = json.loads(resp.read().decode('utf-8'))
    for t in tabs:
        if 'flow.google.com' in t.get('url', ''):
            return t['webSocketDebuggerUrl']
    for t in tabs:
        if t.get('type') == 'page':
            return t['webSocketDebuggerUrl']
    raise RuntimeError('Flow page not found')

async def send_cmd(ws, msg_id, method, params=None):
    payload = {'id': msg_id, 'method': method}
    if params:
        payload['params'] = params
    await ws.send(json.dumps(payload))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=15)
        data = json.loads(raw)
        if data.get('id') == msg_id:
            return data.get('result', {})

async def monitor():
    ws_url = get_flow_ws()
    print(f"Connecting to Flow CDP: {ws_url}", flush=True)
    print(f"Target file: {OUT_VIDEO}", flush=True)
    print("Beginning queue polling loop...", flush=True)

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        msg_id = 1
        for poll_idx in range(60): # poll for up to 10 minutes (60 * 10s)
            script = """(() => {
                const vids = Array.from(document.querySelectorAll('video'))
                    .map(v => v.currentSrc || v.src)
                    .filter(s => s && s.startsWith('http'));

                const body = document.body.innerText || '';
                const match = body.match(/(\\d+)\\s*%/);
                const isGenerating = body.includes('Beenden') || body.includes('Generierung') || !!match;

                // Also check any download buttons or video cards
                const videoCards = Array.from(document.querySelectorAll('flow-video-tile, .video-container, [aria-label*="Video"]')).length;

                return {
                    vids,
                    pct: match ? match[1] : null,
                    isGenerating,
                    videoCards
                };
            })()"""

            res = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': script, 'returnByValue': True})
            msg_id += 1
            info = res.get('result', {}).get('value', {})
            vids = info.get('vids', [])
            pct = info.get('pct')
            cards = info.get('videoCards', 0)

            elapsed = poll_idx * 10
            if pct:
                print(f"[{elapsed}s] Veo generation progress: {pct}%", flush=True)
            elif vids:
                print(f"[{elapsed}s] Video URL detected: {vids[-1]}", flush=True)
                # Download video via evaluate fetch
                dl_script = f"""(async () => {{
                    const resp = await fetch("{vids[-1]}");
                    const blob = await resp.blob();
                    return new Promise((resolve) => {{
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    }});
                }})()"""
                dl_res = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': dl_script, 'returnByValue': True, 'awaitPromise': True})
                msg_id += 1
                b64_data = dl_res.get('result', {}).get('value', '')
                if b64_data and ',' in b64_data:
                    import base64
                    raw_bytes = base64.b64decode(b64_data.split(',')[1])
                    with open(OUT_VIDEO, 'wb') as f:
                        f.write(raw_bytes)
                    print(f"SUCCESS! Downloaded video to {OUT_VIDEO} ({len(raw_bytes)} bytes)", flush=True)
                    break
            elif cards > 0 and poll_idx > 6:
                print(f"[{elapsed}s] {cards} video cards found on canvas. Extracting video elements...", flush=True)
                # Click on the latest card to mount video player
                click_script = """(() => {
                    const tiles = document.querySelectorAll('flow-video-tile, .video-container');
                    if (tiles.length > 0) {
                        tiles[tiles.length - 1].click();
                        return true;
                    }
                    return false;
                })()"""
                await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': click_script, 'returnByValue': True})
                msg_id += 1
            else:
                print(f"[{elapsed}s] Waiting in queue... (video cards: {cards})", flush=True)

            await asyncio.sleep(10)

    # QA extraction if file saved
    if os.path.exists(OUT_VIDEO) and os.path.getsize(OUT_VIDEO) > 10000:
        print("Extracting QA verification frames (25%, 50%, 75%)...")
        try:
            dur_out = subprocess.check_output(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{OUT_VIDEO}"', shell=True, text=True).strip()
            dur = float(dur_out) if dur_out else 8.0
            for pct_val in [25, 50, 75]:
                t = round(dur * (pct_val / 100.0), 2)
                qa_img = f"d:/Projects/VideoGenerator/kuda_idu_frames/clips/clip_01_qa{pct_val}.png"
                subprocess.run(f'ffmpeg -y -ss {t} -i "{OUT_VIDEO}" -frames:v 1 "{qa_img}"', shell=True, capture_output=True)
                print(f"QA {pct_val}% saved to {qa_img}")
        except Exception as e:
            print(f"QA extraction note: {e}")

if __name__ == '__main__':
    asyncio.run(monitor())
