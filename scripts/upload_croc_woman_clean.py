import asyncio
import json
import urllib.request
import websockets
import os
import time

TARGET_IMG = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\references_crocodiles\croc_woman_cand1_1280x720.png")
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

        await call_cdp("Page.enable")
        await call_cdp("DOM.enable")
        await call_cdp("Page.setInterceptFileChooserDialog", {"enabled": True})

        # Find and click 'Hochladen' in the top-right menu or 'Medien hoch...' in dialog
        print("Clicking Hochladen button...", flush=True)
        click_hochladen = """
        (() => {
            // First look for 'Hochladen' in menu
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button'));
            const hochItem = items.find(i => (i.innerText || '').trim() === 'Hochladen');
            if (hochItem) {
                hochItem.click();
                return 'Clicked Hochladen in menu';
            }
            // Or look for 'Medien hoch...' button in popover
            const medienBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('Medien hoch'));
            if (medienBtn) {
                medienBtn.click();
                return 'Clicked Medien hoch... in popover';
            }
            return 'Neither found';
        })()
        """
        res_h = await call_cdp("Runtime.evaluate", {"expression": click_hochladen, "returnByValue": True})
        print("Click result:", res_h.get("result", {}).get("value"))

        # Wait for fileChooserOpened
        print("Waiting for file chooser...", flush=True)
        chosen = False
        for _ in range(10):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                msg = json.loads(raw)
                if msg.get("method") == "Page.fileChooserOpened":
                    print("fileChooserOpened intercepted!", flush=True)
                    backend_id = msg["params"].get("backendNodeId")
                    set_params = {"files": [TARGET_IMG]}
                    if backend_id:
                        set_params["backendNodeId"] = backend_id
                    await call_cdp("DOM.setFileInputFiles", set_params)
                    print("DOM.setFileInputFiles successfully sent!", flush=True)
                    chosen = True
                    break
            except asyncio.TimeoutError:
                pass

        if not chosen:
            print("Trying direct input[type=file]...", flush=True)
            doc = await call_cdp("DOM.getDocument")
            file_input = await call_cdp("DOM.querySelector", {
                "nodeId": doc["root"]["nodeId"],
                "selector": "input[type=\"file\"]"
            })
            if file_input and file_input.get("nodeId"):
                await call_cdp("DOM.setFileInputFiles", {
                    "files": [TARGET_IMG],
                    "nodeId": file_input["nodeId"]
                })
                print("Direct input[type=file] succeeded!", flush=True)

        print("Waiting 5s for Flow to upload and register file...")
        await asyncio.sleep(5.0)
        print("Upload process finished!")

if __name__ == "__main__":
    asyncio.run(main())
