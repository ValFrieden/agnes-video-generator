import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        # Hover over the image tile or click it
        hover_script = """
        (() => {
            const img = document.querySelector('img[src*="flow.google.com/asb"]');
            if (img) {
                const rect = img.getBoundingClientRect();
                return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
            }
            return null;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': hover_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        coords = res['result']['result']['value']
        print("Image coords:", coords)
        
        # Click on the image
        await ws.send(json.dumps({'id': 2, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': coords['x'], 'y': coords['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 3, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': coords['x'], 'y': coords['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await asyncio.sleep(1)

        # Check what opened
        check_open = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, [role="button"], .action-button')).map(b => ({
                text: (b.innerText || '').trim(),
                aria: b.getAttribute('aria-label')
            })).filter(b => b.text || b.aria);
            return btns.slice(-15);
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': check_open, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Buttons after clicking image:", json.dumps(res2['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check())
