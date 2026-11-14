import asyncio
import json
import urllib.request
import websockets
import os

async def main():
    abs_path = os.path.abspath('nikogda_ne_boyus_frames/firefighter_cand2_1280x720.png')
    print("Target file to upload:", abs_path)
    assert os.path.exists(abs_path), f"File missing: {abs_path}"

    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Tab URL:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
        await ws.recv()

        await ws.send(json.dumps({'id': 2, 'method': 'Page.setInterceptFileChooserDialog', 'params': {'enabled': True}}))
        await ws.recv()

        # Get coords of top-right "Medien hinzufügen"
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
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': get_menu_coords, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        c = res['result']['result']['value']
        print("Menu button coords:", c)

        # Click menu button via mouse
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await asyncio.sleep(0.6)

        # Get coords of Hochladen
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
        await ws.send(json.dumps({'id': 20, 'method': 'Runtime.evaluate', 'params': {'expression': get_h_coords, 'returnByValue': True}}))
        res_h = json.loads(await ws.recv())
        h_coords = res_h['result']['result']['value']
        print("Hochladen coords:", h_coords)

        if not h_coords:
            print("ERROR: Hochladen button not found!")
            return

        # Click Hochladen via mouse
        await ws.send(json.dumps({'id': 30, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': h_coords['x'], 'y': h_coords['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 31, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': h_coords['x'], 'y': h_coords['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        print("Dispatched mouse click on Hochladen! Waiting for fileChooserOpened...")

        file_set = False
        for i in range(20):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                msg = json.loads(raw)
                print("Received event:", msg.get('method'))
                if msg.get('method') == 'Page.fileChooserOpened':
                    print("SUCCESS! Intercepted Page.fileChooserOpened! Sending file...")
                    await ws.send(json.dumps({
                        'id': 100,
                        'method': 'Page.handleFileChooser',
                        'params': {
                            'action': 'accept',
                            'files': [abs_path]
                        }
                    }))
                    print("handleFileChooser reply:", await ws.recv())
                    file_set = True
                    break
            except asyncio.TimeoutError:
                pass

        if file_set:
            print("File accepted! Waiting 5s for Flow to process upload...")
            await asyncio.sleep(5)
            print("Upload complete!")
        else:
            print("FileChooser still not triggered.")

if __name__ == '__main__':
    asyncio.run(main())
