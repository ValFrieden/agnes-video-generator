import asyncio
import json
import urllib.request
import websockets
import os
import base64

async def main():
    target_file = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\firefighter_cand2_1280x720.png")
    print("Uploading target file:", target_file)
    assert os.path.exists(target_file), f"File not found: {target_file}"

    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        # Step 1: Close any open popups or menus with Escape
        await ws.send(json.dumps({'id': 1, 'method': 'Input.dispatchKeyEvent', 'params': {'type': 'keyDown', 'key': 'Escape'}}))
        await ws.recv()
        await asyncio.sleep(0.3)

        # Step 2: Enable Page and file chooser interception
        await ws.send(json.dumps({'id': 2, 'method': 'Page.enable'}))
        await ws.recv()
        await ws.send(json.dumps({'id': 3, 'method': 'Page.setInterceptFileChooserDialog', 'params': {'enabled': True}}))
        await ws.recv()

        # Step 3: Click 'Medien hinzufügen' button
        click_add = """
        (() => {
            const btn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
            if (btn) {
                btn.click();
                return 'CLICKED_ADD_MEDIA';
            }
            return 'NOT_FOUND';
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': click_add, 'returnByValue': True}}))
        res_add = json.loads(await ws.recv())
        print("Click Add Media:", res_add['result']['result']['value'])
        await asyncio.sleep(0.6)

        # Step 4: Click 'Hochladen' in the popup menu
        click_hoch = """
        (() => {
            const items = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const uploadBtn = items.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (uploadBtn) {
                (uploadBtn.closest('button') || uploadBtn).click();
                return 'CLICKED_HOCHLADEN';
            }
            return 'HOCHLADEN_NOT_FOUND';
        })()
        """
        await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': click_hoch, 'returnByValue': True}}))
        res_h = json.loads(await ws.recv())
        print("Click Hochladen:", res_h['result']['result']['value'])

        # Step 5: Wait for fileChooserOpened
        file_set = False
        for _ in range(20):
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=1.5))
                if msg.get('method') == 'Page.fileChooserOpened':
                    print("Intercepted Page.fileChooserOpened! Sending file path...", flush=True)
                    await ws.send(json.dumps({
                        'id': 100,
                        'method': 'Page.handleFileChooser',
                        'params': {
                            'action': 'accept',
                            'files': [target_file]
                        }
                    }))
                    res_fc = json.loads(await ws.recv())
                    print("handleFileChooser response:", res_fc)
                    file_set = True
                    break
            except asyncio.TimeoutError:
                pass

        if file_set:
            print("File accepted by browser! Waiting 6s for Flow upload...", flush=True)
            await asyncio.sleep(6.0)
            print("Done uploading!")
        else:
            print("ERROR: FileChooser was not triggered!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
