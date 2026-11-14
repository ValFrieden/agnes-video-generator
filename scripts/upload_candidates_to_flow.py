import asyncio
import json
import urllib.request
import websockets
import os

async def upload_file(ws, abs_path):
    print(f"\n--- Uploading {abs_path} ---")
    assert os.path.exists(abs_path), f"File missing: {abs_path}"

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
    if not c:
        print("Menu button not found!")
        return False

    # Click menu button
    await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
    await ws.recv()
    await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
    await ws.recv()
    await asyncio.sleep(0.6)

    # Find Hochladen coords
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
    await ws.send(json.dumps({'id': 12, 'method': 'Runtime.evaluate', 'params': {'expression': get_h_coords, 'returnByValue': True}}))
    res2 = json.loads(await ws.recv())
    hc = res2['result']['result']['value']
    if not hc:
        print("Hochladen button not found!")
        return False

    print("Clicking Hochladen at:", hc)
    # Listen for file chooser event
    click_task = asyncio.create_task(ws.send(json.dumps({
        'id': 14,
        'method': 'Input.dispatchMouseEvent',
        'params': {'type': 'mousePressed', 'x': hc['x'], 'y': hc['y'], 'button': 'left', 'clickCount': 1}
    })))
    await click_task
    await ws.recv()
    await ws.send(json.dumps({
        'id': 15,
        'method': 'Input.dispatchMouseEvent',
        'params': {'type': 'mouseReleased', 'x': hc['x'], 'y': hc['y'], 'button': 'left', 'clickCount': 1}
    }))
    await ws.recv()

    # Wait for fileChooserOpened event
    print("Waiting for Page.fileChooserOpened...")
    for _ in range(15):
        msg = json.loads(await ws.recv())
        if msg.get('method') == 'Page.fileChooserOpened':
            print("Intercepted Page.fileChooserOpened event successfully!")
            backend_id = msg['params'].get('backendNodeId')
            await ws.send(json.dumps({
                'id': 20,
                'method': 'DOM.setFileInputFiles',
                'params': {
                    'files': [abs_path],
                    'backendNodeId': backend_id
                }
            }))
            res_file = json.loads(await ws.recv())
            print("DOM.setFileInputFiles response:", res_file)
            await asyncio.sleep(2.0)
            return True
    return False

async def main():
    files = [
        os.path.abspath('nikogda_ne_boyus_frames/climber_organic_cand1_1280x720.png'),
        os.path.abspath('nikogda_ne_boyus_frames/climber_organic_cand2_1280x720.png')
    ]

    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Connecting to Flow Tab:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        for f in files:
            ok = await upload_file(ws, f)
            print("Uploaded:", f, "->", ok)
            await asyncio.sleep(2.0)

if __name__ == '__main__':
    asyncio.run(main())
