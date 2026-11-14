import asyncio
import json
import urllib.request
import websockets
import base64

async def select_and_add():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Click the image at x: 564, y: 624
        print("Clicking target image at (564, 624)...")
        await ws.send(json.dumps({'id': 1, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 564, 'y': 624, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 2, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 564, 'y': 624, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await asyncio.sleep(1)

        # Step 2: Take screenshot to see if action menu or viewer opened
        await ws.send(json.dumps({'id': 3, 'method': 'Page.captureScreenshot'}))
        res = json.loads(await ws.recv())
        with open('after_image_click.png', 'wb') as f:
            f.write(base64.b64decode(res['result']['data']))
        print("Saved after_image_click.png")

        # Step 3: Check visible buttons/menus
        expr = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, [role="button"], span, .mat-mdc-menu-item'))
                .filter(b => {
                    const r = b.getBoundingClientRect();
                    return r.width > 0 && r.height > 0 && (b.innerText || '').trim().length > 0;
                })
                .map(b => ({ text: b.innerText.trim(), x: b.getBoundingClientRect().x, y: b.getBoundingClientRect().y, disabled: b.disabled }));
            return btns;
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        btns = json.loads(await ws.recv())
        print("Active visible buttons:")
        for b in btns['result']['result']['value']:
            if any(k in b['text'] for k in ['Prompt', 'Hinzufügen', 'Bearbeiten', 'Löschen', 'Verwenden', 'Add']):
                print(" ->", b)

if __name__ == '__main__':
    asyncio.run(select_and_add())
