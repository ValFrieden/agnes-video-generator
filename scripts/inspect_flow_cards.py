import asyncio
import json
import urllib.request
import websockets

async def inspect_gallery():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const cards = Array.from(document.querySelectorAll('img, [role="img"], .media-card, .asset-card, div[class*="tile"], div[class*="card"]'))
                .filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.width > 150 && r.height > 100 && r.left > 100 && r.right < 1400;
                })
                .map(el => {
                    const r = el.getBoundingClientRect();
                    return {
                        tag: el.tagName,
                        className: el.className,
                        src: el.src || (el.querySelector('img') ? el.querySelector('img').src : null),
                        x: r.x + r.width / 2,
                        y: r.y + r.height / 2,
                        width: r.width,
                        height: r.height
                    };
                });
            return cards;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Cards in gallery:", json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(inspect_gallery())
