import asyncio
import json
import urllib.request
import websockets

async def click_download_icon():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button')).map(b => {
                const r = b.getBoundingClientRect();
                return {
                    text: (b.innerText || '').trim(),
                    aria: b.getAttribute('aria-label'),
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2,
                    w: r.width,
                    h: r.height
                };
            }).filter(b => (b.text + ' ' + (b.aria || '')).toLowerCase().includes('download') || (b.aria || '').includes('herunterladen'));
            return btns;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        val = res['result']['result']['value']
        print('Download buttons found:', val)
        
        for b in val:
            if b['x'] > 1000 and b['y'] < 100:
                print(f"Clicking download button at ({b['x']}, {b['y']})...")
                await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': b['x'], 'y': b['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': b['x'], 'y': b['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                print('Dispatched click!')

if __name__ == '__main__':
    asyncio.run(click_download_icon())
