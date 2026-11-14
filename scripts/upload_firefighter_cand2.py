import asyncio
import json
import urllib.request
import websockets
import os
import time

TARGET_IMG = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\firefighter_cand2_1280x720.png")
print("Target file to upload:", TARGET_IMG, "Exists:", os.path.exists(TARGET_IMG))

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    ws_url = flow_tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        async def call_cdp(method, params=None):
            cid = int(time.time() * 1000) % 1000000
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=6.0)
                    msg = json.loads(raw)
                    if msg.get("id") == cid:
                        return msg.get("result", {})
                except asyncio.TimeoutError:
                    return None

        # 1. Close open popovers first
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.3)
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.5)

        await call_cdp("Page.enable")
        await call_cdp("Page.setInterceptFileChooserDialog", {"enabled": True})

        # 2. Click 'Medien hinzufügen' (+) button at top right
        click_add = """
        (() => {
            const btn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
            if (btn) {
                btn.click();
                return 'Clicked Medien hinzufügen button';
            }
            return 'Not found';
        })()
        """
        res_a = await call_cdp("Runtime.evaluate", {"expression": click_add, "returnByValue": True})
        print("Click add button:", res_a.get("result", {}).get("value"))
        await asyncio.sleep(0.8)

        # 3. Click 'Hochladen' in the dropdown menu
        click_hoch = """
        (() => {
            const items = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const uploadBtn = items.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (uploadBtn) {
                uploadBtn.click();
                return 'Clicked Hochladen in menu';
            }
            return 'Hochladen not found';
        })()
        """
        res_h = await call_cdp("Runtime.evaluate", {"expression": click_hoch, "returnByValue": True})
        print("Click Hochladen:", res_h.get("result", {}).get("value"))

        # 4. Handle file chooser
        file_set = False
        for _ in range(15):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                msg = json.loads(raw)
                if msg.get("method") == "Page.fileChooserOpened":
                    print("Intercepted Page.fileChooserOpened! Sending file path...", flush=True)
                    await ws.send(json.dumps({
                        "id": 100,
                        "method": "Page.handleFileChooser",
                        "params": {
                            "action": "accept",
                            "files": [TARGET_IMG]
                        }
                    }))
                    print("handleFileChooser sent:", await ws.recv(), flush=True)
                    file_set = True
                    break
            except asyncio.TimeoutError:
                pass

        if file_set:
            print("File accepted! Waiting 6s for upload to process in Flow...", flush=True)
            await asyncio.sleep(6.0)
            print("Done uploading firefighter_cand2!")
        else:
            print("ERROR: FileChooser event was not triggered!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
