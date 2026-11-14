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
            const items = Array.from(document.querySelectorAll('.asset-item, .library-item, .media-card, [class*="thumbnail"], [class*="item"]'))
                .filter(el => el.getBoundingClientRect().width > 20 && el.getBoundingClientRect().height > 20)
                .map(el => ({
                    tag: el.tagName,
                    class: el.className,
                    text: (el.innerText || '').trim(),
                    aria: el.getAttribute('aria-label'),
                    rect: el.getBoundingClientRect()
                }));
            return items.slice(0, 30);
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check())
