import asyncio
import json
import urllib.request
import websockets

async def check_chip():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const chips = Array.from(document.querySelectorAll('.chip-container, [aria-label="Bildelement"]'));
            return chips.map(c => {
                const img = c.querySelector('img');
                const btn = c.querySelector('button');
                return {
                    imgSrc: img ? img.src : null,
                    text: c.innerText,
                    hasRemoveBtn: !!btn
                };
            });
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Chip details:", json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check_chip())
