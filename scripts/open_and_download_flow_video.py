import asyncio
import json
import urllib.request
import websockets
import base64
import os

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Click the video container at (1676, 603)
        print("Opening video in editor...")
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 1676, 'y': 603, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 1676, 'y': 603, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await asyncio.sleep(1.5)

        # Inspect the editor for video source / download button
        script = """
        (() => {
            const vid = document.querySelector('video');
            const btns = Array.from(document.querySelectorAll('button, a')).map(b => {
                const r = b.getBoundingClientRect();
                return {
                    text: (b.innerText || '').trim(),
                    aria: b.getAttribute('aria-label'),
                    href: b.href,
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2
                };
            }).filter(b => (b.text + ' ' + (b.aria || '') + ' ' + (b.href || '')).toLowerCase().includes('download') || (b.aria || '').includes('herunterladen'));

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
        with open('video_editor_screen.png', 'wb') as f:
            f.write(base64.b64decode(sc_res['result']['data']))
        print("Saved video_editor_screen.png")

if __name__ == '__main__':
    asyncio.run(main())
