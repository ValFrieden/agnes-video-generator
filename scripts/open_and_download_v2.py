import asyncio
import json
import urllib.request
import websockets
import base64
import os
import shutil

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Tab:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Click the top-left video tile
        print("Clicking top-left video tile at (x: 290, y: 270)...")
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 290, 'y': 270, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 290, 'y': 270, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await asyncio.sleep(2)

        # Step 2: Inspect editor state
        script = """
        (() => {
            const vid = document.querySelector('video');
            const btns = Array.from(document.querySelectorAll('button, a')).map(b => {
                const r = b.getBoundingClientRect();
                return {
                    text: (b.innerText || '').trim(),
                    aria: b.getAttribute('aria-label'),
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2
                };
            }).filter(b => (b.text + ' ' + (b.aria || '')).toLowerCase().includes('download') || (b.aria || '').toLowerCase().includes('herunterladen') || (b.aria || '').toLowerCase().includes('download'));

            return {
                videoSrc: vid ? (vid.src || vid.currentSrc) : null,
                downloadBtns: btns
            };
        })()
        """
        await ws.send(json.dumps({'id': 20, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        val = res['result']['result']['value']
        print("Editor video info:", json.dumps(val, indent=2))

        # Take screenshot of editor
        await ws.send(json.dumps({'id': 30, 'method': 'Page.captureScreenshot'}))
        sc_res = json.loads(await ws.recv())
        with open('editor_screen_v2.png', 'wb') as f:
            f.write(base64.b64decode(sc_res['result']['data']))
        print("Saved editor_screen_v2.png")

        # Step 3: Download video
        # If there's a download button, click it
        dl_btns = val.get('downloadBtns', [])
        if dl_btns:
            btn = dl_btns[0]
            print(f"Clicking download button at ({btn['x']}, {btn['y']})...")
            await ws.send(json.dumps({'id': 40, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': btn['x'], 'y': btn['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 41, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': btn['x'], 'y': btn['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Download button clicked!")
        else:
            print("No download button found directly; checking videoSrc...")

if __name__ == '__main__':
    asyncio.run(main())
