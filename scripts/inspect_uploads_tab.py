import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        click_uploads = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, a'));
            const b = btns.find(el => (el.innerText || '').includes('Uploads'));
            if (b) {
                b.click();
                return 'Clicked Uploads';
            }
            return 'Uploads not found';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_uploads, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])
        await asyncio.sleep(1)

        # Inspect elements
        script = """
        (() => {
            const cards = Array.from(document.querySelectorAll('img, video, [class*="card"], [class*="tile"], [class*="asset"]')).map(el => ({
                tag: el.tagName,
                src: el.src,
                class: el.className,
                aria: el.getAttribute('aria-label'),
                text: (el.innerText || '').trim()
            })).filter(x => x.src || x.aria || x.text);
            return cards.slice(0, 20);
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Uploads view:", json.dumps(res2['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check())
