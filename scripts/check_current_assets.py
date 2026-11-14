import asyncio, json, urllib.request, websockets

async def check_assets():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        js = """
        (() => {
            const cards = Array.from(document.querySelectorAll('.asset-card, .asset-list-item, [class*="asset"]')).map(el => el.innerText.trim()).filter(Boolean);
            const imgs = Array.from(document.querySelectorAll('img')).map(i => i.alt || i.src).slice(0, 10);
            return { title: document.title, cards: cards.slice(0, 10), imgs };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print(json.dumps(msg['result']['result']['value'], indent=2))
                break

asyncio.run(check_assets())
