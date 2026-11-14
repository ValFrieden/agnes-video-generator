import asyncio
import json
import urllib.request
import websockets
import os
import shutil
import time

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Click "Medien herunterladen"
        print("Clicking download button in header...")
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 1557.6, 'y': 38, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 1557.6, 'y': 38, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await asyncio.sleep(0.5)

        # Inspect menu options
        script = """
        (() => {
            const els = Array.from(document.querySelectorAll('.mat-mdc-menu-panel *, [role="menu"] *, [role="menuitem"], button, div'));
            const options = els.filter(e => {
                const txt = (e.innerText || '').trim();
                return (txt.includes('720') || txt.includes('1080') || txt.includes('MP4') || txt.includes('Video') || txt.includes('Herunterladen')) && e.children.length === 0;
            }).map(e => {
                const r = e.getBoundingClientRect();
                return {
                    text: e.innerText.trim(),
                    tag: e.tagName,
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2,
                    w: r.width,
                    h: r.height
                };
            }).filter(e => e.w > 0 && e.h > 0);
            return options;
        })()
        """
        await ws.send(json.dumps({'id': 20, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        options = res['result']['result']['value']
        print("Download menu options:", json.dumps(options, indent=2))

        # Find best option: 720p or whatever is available
        opt = next((o for o in options if '720p' in o['text']), None)
        if not opt and options:
            opt = options[0]

        if opt:
            print(f"Clicking option: {opt['text']} at ({opt['x']}, {opt['y']})...")
            await ws.send(json.dumps({'id': 30, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': opt['x'], 'y': opt['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 31, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': opt['x'], 'y': opt['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Download option clicked!")

if __name__ == '__main__':
    asyncio.run(main())
