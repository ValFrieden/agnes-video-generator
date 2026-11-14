import asyncio
import json
import urllib.request
import websockets
import os
import time

TARGET_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips"
os.makedirs(TARGET_DIR, exist_ok=True)

async def trigger_download():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    ws_url = flow_tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        async def call_cdp(method, params=None):
            cid = int(time.time() * 1000) % 1000000
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    msg = json.loads(raw)
                    if msg.get("id") == cid:
                        return msg.get("result", {})
                except asyncio.TimeoutError:
                    return None

        # 1. Enable Browser/Page download behavior
        print("Configuring download behavior to:", TARGET_DIR)
        await call_cdp("Browser.setDownloadBehavior", {
            "behavior": "allowAndName",
            "downloadPath": TARGET_DIR,
            "eventsEnabled": True
        })
        await call_cdp("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": TARGET_DIR
        })

        # 2. Click download button
        click_dl = """
        (() => {
            const btn = document.querySelector('button[aria-label="Herunterladen"]') || 
                        document.querySelector('button[aria-label="Medien herunterladen"]') ||
                        Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').trim() === 'download');
            if (btn) {
                btn.click();
                return { success: true, aria: btn.getAttribute('aria-label') };
            }
            return { error: 'No download button' };
        })()
        """
        res = await call_cdp("Runtime.evaluate", {"expression": click_dl, "returnByValue": True})
        print("Download button click:", res.get("result", {}).get("value"))

        await asyncio.sleep(1.0)

        # 3. Check if menu opened and click the item (e.g. MP4, 720p, Video)
        click_menu_item = """
        (() => {
            const menu = document.querySelector('.mat-mdc-menu-panel, [role="menu"]');
            if (!menu) {
                // If no menu, maybe download already triggered
                return { menuFound: false };
            }
            const items = Array.from(menu.querySelectorAll('[role="menuitem"], button, .mat-mdc-menu-item'));
            const itemTexts = items.map(i => (i.innerText || '').trim());
            // Click the first video/mp4/720p option, or first item
            const target = items.find(i => {
                const t = (i.innerText || '').toLowerCase();
                return t.includes('mp4') || t.includes('720') || t.includes('video');
            }) || items[0];

            if (target) {
                target.click();
                return { menuFound: true, clicked: target.innerText, allItems: itemTexts };
            }
            return { menuFound: true, allItems: itemTexts };
        })()
        """
        res_menu = await call_cdp("Runtime.evaluate", {"expression": click_menu_item, "returnByValue": True})
        print("Menu item click:", res_menu.get("result", {}).get("value"))

        # 4. Wait for file to appear in TARGET_DIR
        print("Waiting for downloaded file...")
        initial_files = set(os.listdir(TARGET_DIR))
        for _ in range(30):
            await asyncio.sleep(1.0)
            current_files = set(os.listdir(TARGET_DIR))
            new_files = [f for f in (current_files - initial_files) if not f.endswith('.crdownload') and not f.endswith('.tmp')]
            if new_files:
                new_file = new_files[0]
                print(f"Downloaded file: {new_file}")
                return os.path.join(TARGET_DIR, new_file)

        return None

if __name__ == "__main__":
    result = asyncio.run(trigger_download())
    print("Download result path:", result)
