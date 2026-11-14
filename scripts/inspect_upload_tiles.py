import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        script = """
        (() => {
            const tiles = Array.from(document.querySelectorAll('.media-gallery-item, .asset-tile, [class*="card"], [class*="item"]')).filter(el => {
                const r = el.getBoundingClientRect();
                return r.x > 200 && r.y > 50 && r.width > 50 && r.height > 50;
            }).map(el => {
                const img = el.querySelector('img');
                const r = el.getBoundingClientRect();
                return {
                    text: (el.innerText || '').trim(),
                    imgSrc: img ? img.src : null,
                    aria: el.getAttribute('aria-label'),
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2
                };
            });
            return tiles.slice(0, 10);
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check())
