import asyncio
import json
import urllib.request
import websockets
import os
import sys
import time
import shutil

CLIPS_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips"
os.makedirs(CLIPS_DIR, exist_ok=True)
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

async def poll_video():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    ws_url = flow_tab["webSocketDebuggerUrl"]

    print("Polling Flow for completed Crocodiles video...", flush=True)

    check_js = """
    (() => {
        // Find all videos in page
        const videos = Array.from(document.querySelectorAll('video')).map(v => ({
            src: v.src || v.currentSrc,
            duration: v.duration,
            paused: v.paused
        }));

        // Find clickable video containers in chat
        const videoCards = Array.from(document.querySelectorAll('.video-container, [aria-label*="Video im Editor"], [aria-label*="Play"]')).map(el => ({
            aria: el.getAttribute('aria-label'),
            className: el.className
        }));

        const body = document.body.innerText;
        const matchPercent = body.match(/(\\d+)\\s*%/);
        const percent = matchPercent ? matchPercent[1] : null;

        // Check if video is finished in chat text
        const hasFinished = body.includes('finished') || body.includes('Fertig') || body.includes('hier ist dein Video') || body.includes('generated your video');

        return {
            videoCount: videos.length,
            videos,
            videoCards,
            percent,
            hasFinished
        };
    })()
    """

    for iteration in range(60): # up to 10 minutes
        try:
            async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
                cid = 300 + iteration
                await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": check_js, "returnByValue": True}}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                res = json.loads(raw).get("result", {}).get("result", {}).get("value", {})
                
                print(f"[{time.strftime('%H:%M:%S')}] Check #{iteration+1}: Videos={res.get('videoCount')}, VideoCards={len(res.get('videoCards', []))}, Percent={res.get('percent')}%", flush=True)

                # Check if there is a new video card in chat
                if len(res.get("videoCards", [])) > 0:
                    print(">>> Found video card in chat! Opening editor to download...", flush=True)
                    # Click video card to open editor
                    click_card = """
                    (() => {
                        const card = document.querySelector('.video-container, [aria-label*="Video im Editor"]');
                        if (card) {
                            card.click();
                            return 'Clicked video card';
                        }
                        return 'No card';
                    })()
                    """
                    cid_c = 400 + iteration
                    await ws.send(json.dumps({"id": cid_c, "method": "Runtime.evaluate", "params": {"expression": click_card, "returnByValue": True}}))
                    await ws.recv()
                    await asyncio.sleep(2.0)

                    # Configure download behavior
                    await ws.send(json.dumps({
                        "id": 501,
                        "method": "Page.setDownloadBehavior",
                        "params": {"behavior": "allow", "downloadPath": CLIPS_DIR}
                    }))
                    await ws.recv()

                    # Click download button
                    click_dl = """
                    (() => {
                        const btn = document.querySelector('button[aria-label="Herunterladen"]') || 
                                    document.querySelector('button[aria-label="Medien herunterladen"]') ||
                                    Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').trim() === 'download');
                        if (btn) {
                            btn.click();
                            return { success: true };
                        }
                        return { error: 'No dl btn' };
                    })()
                    """
                    cid_d = 502
                    await ws.send(json.dumps({"id": cid_d, "method": "Runtime.evaluate", "params": {"expression": click_dl, "returnByValue": True}}))
                    await ws.recv()
                    await asyncio.sleep(1.0)

                    # Click 720p / MP4 in menu
                    click_menu = """
                    (() => {
                        const menu = document.querySelector('.mat-mdc-menu-panel, [role="menu"]');
                        if (!menu) return { menuFound: false };
                        const items = Array.from(menu.querySelectorAll('[role="menuitem"], button'));
                        const target = items.find(i => (i.innerText || '').toLowerCase().includes('720')) || items[0];
                        if (target) {
                            target.click();
                            return { success: true, text: target.innerText };
                        }
                        return { error: 'No item' };
                    })()
                    """
                    cid_m = 503
                    await ws.send(json.dumps({"id": cid_m, "method": "Runtime.evaluate", "params": {"expression": click_menu, "returnByValue": True}}))
                    await ws.recv()

                    # Wait for downloaded file in CLIPS_DIR
                    print("Waiting for file download...")
                    initial_files = set(os.listdir(CLIPS_DIR))
                    for _ in range(30):
                        await asyncio.sleep(1.0)
                        curr = set(os.listdir(CLIPS_DIR))
                        new_f = [f for f in (curr - initial_files) if not f.endswith('.crdownload') and not f.endswith('.tmp') and f.endswith('.mp4')]
                        if new_f:
                            downloaded = os.path.join(CLIPS_DIR, new_f[0])
                            print(f">>> DOWNLOAD COMPLETE: {downloaded}", flush=True)
                            return downloaded

        except Exception as e:
            print(f"Error in poll: {e}", flush=True)

        await asyncio.sleep(10)

    return None

if __name__ == "__main__":
    res = asyncio.run(poll_video())
    print("Final result:", res)
