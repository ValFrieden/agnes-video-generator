import asyncio
import json
import urllib.request
import websockets
import os
import time

TARGET_IMG = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\firefighter_cand2_1280x720.png")
print("Target image to upload:", TARGET_IMG, "Exists:", os.path.exists(TARGET_IMG))

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
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

        # 1. Close open popovers with Escape
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.3)
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.5)

        await call_cdp("Page.enable")
        await call_cdp("DOM.enable")
        await call_cdp("Page.setInterceptFileChooserDialog", {"enabled": True})

        # 2. Get coords of top-right "Medien hinzufügen"
        get_menu_coords = """
        (() => {
            const btn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
            if (btn) {
                const r = btn.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
            return null;
        })()
        """
        res_btn = await call_cdp("Runtime.evaluate", {"expression": get_menu_coords, "returnByValue": True})
        c = res_btn.get("result", {}).get("value")
        print("Menu button coords:", c)

        # 3. Mouse click on Menu button
        await call_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": c["x"], "y": c["y"], "button": "left", "clickCount": 1})
        await call_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": c["x"], "y": c["y"], "button": "left", "clickCount": 1})
        await asyncio.sleep(0.6)

        # 4. Get coords of "Hochladen" menuitem
        get_h_coords = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const b = btns.find(el => (el.innerText || '').trim() === 'Hochladen' || (el.innerText || '').includes('Hochladen'));
            if (b) {
                const r = b.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
            return null;
        })()
        """
        res_h = await call_cdp("Runtime.evaluate", {"expression": get_h_coords, "returnByValue": True})
        h_coords = res_h.get("result", {}).get("value")
        print("Hochladen coords:", h_coords)

        # 5. Mouse click on "Hochladen"
        await call_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": h_coords["x"], "y": h_coords["y"], "button": "left", "clickCount": 1})
        await call_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": h_coords["x"], "y": h_coords["y"], "button": "left", "clickCount": 1})
        print("Clicked Hochladen! Waiting for file chooser event...", flush=True)

        # 6. Intercept fileChooserOpened and send DOM.setFileInputFiles
        file_set = False
        for _ in range(15):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                msg = json.loads(raw)
                if msg.get("method") == "Page.fileChooserOpened":
                    print("Intercepted Page.fileChooserOpened!", flush=True)
                    backend_id = msg["params"].get("backendNodeId")
                    set_params = {"files": [TARGET_IMG]}
                    if backend_id:
                        set_params["backendNodeId"] = backend_id
                    res_set = await call_cdp("DOM.setFileInputFiles", set_params)
                    print("DOM.setFileInputFiles result:", res_set, flush=True)
                    file_set = True
                    break
            except asyncio.TimeoutError:
                pass

        if file_set:
            print("File delivered! Waiting 7s for Flow to upload and register asset...", flush=True)
            await asyncio.sleep(7.0)
            print("Upload process completed successfully!", flush=True)
        else:
            print("ERROR: fileChooserOpened not intercepted!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
