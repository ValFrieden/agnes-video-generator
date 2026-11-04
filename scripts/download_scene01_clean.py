import asyncio
import json
import urllib.request
import websockets
import os
import time

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

OUT_DIR = os.path.abspath("moy_mir_iz_snov_frames")

async def download_video():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        # Set browser download directory
        await ws.send(json.dumps({
            'id': 1,
            'method': 'Browser.setDownloadBehavior',
            'params': {
                'behavior': 'allowAndName',
                'downloadPath': OUT_DIR,
                'eventsEnabled': True
            }
        }))
        print("Set download path to:", OUT_DIR, json.loads(await ws.recv()))

        # Click the video tile
        click_tile = """(() => {
            const tile = document.querySelector('flow-video-tile') || document.querySelector('[class*="video-tile"]') || document.querySelector('cdk-virtual-scroll-viewport div');
            if (tile) {
                tile.click();
                return 'Clicked video tile';
            }
            return 'Tile not found';
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': click_tile, 'returnByValue': True}}))
        print(json.loads(await ws.recv())['result']['result']['value'])
        await asyncio.sleep(2)

        # Inspect open player buttons
        inspect_player = """(() => {
            const btns = Array.from(document.querySelectorAll('button')).map(b => ({
                text: (b.innerText || '').trim().replace(/\\n+/g, ' '),
                aria: b.getAttribute('aria-label') || '',
                cls: b.className
            }));
            return btns.filter(b => b.text || b.aria);
        })()"""
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': inspect_player, 'returnByValue': True}}))
        btns = json.loads(await ws.recv())['result']['result']['value']
        print("Player buttons found:", json.dumps(btns, indent=2, ensure_ascii=False))

        # Look for Download button
        click_dl = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const dl = btns.find(b => {
                const a = (b.getAttribute('aria-label') || '').toLowerCase();
                const t = (b.innerText || '').toLowerCase();
                return a.includes('herunterladen') || a.includes('download') || t.includes('download');
            });
            if (dl) {
                dl.click();
                return { success: true, aria: dl.getAttribute('aria-label'), text: dl.innerText };
            }
            return { success: false };
        })()"""
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': click_dl, 'returnByValue': True}}))
        dl_res = json.loads(await ws.recv())['result']['result']['value']
        print("Click download button:", dl_res)
        await asyncio.sleep(1.5)

        # Click 720p option in menu
        click_720 = """(() => {
            const items = Array.from(document.querySelectorAll('*'));
            const target = items.find(el => (el.innerText || '').includes('720p'));
            if (target) {
                target.click();
                return { success: true, text: target.innerText };
            }
            return { success: false };
        })()"""
        await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': click_720, 'returnByValue': True}}))
        res_720 = json.loads(await ws.recv())['result']['result']['value']
        print("Click 720p option:", res_720)

        # Wait for file in OUT_DIR or Downloads
        print("Monitoring for new downloaded file...")
        dl_user = os.path.expanduser('~/Downloads')
        for i in range(25):
            await asyncio.sleep(1)
            # check OUT_DIR
            out_files = [f for f in os.listdir(OUT_DIR) if f.endswith('.mp4') and 'clean' in f.lower()]
            # check Downloads
            dl_files = [os.path.join(dl_user, f) for f in os.listdir(dl_user) if f.endswith('.mp4')]
            recent_dl = [f for f in dl_files if time.time() - os.path.getmtime(f) < 30]
            if recent_dl:
                print("Found freshly downloaded file in ~/Downloads:", recent_dl[0])
                target_dest = os.path.join(OUT_DIR, "scene_01_raw_clean.mp4")
                import shutil
                shutil.copy2(recent_dl[0], target_dest)
                print(f"Copied to {target_dest} ({os.path.getsize(target_dest)} bytes)")
                break

if __name__ == '__main__':
    asyncio.run(download_video())
