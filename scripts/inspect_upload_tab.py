import asyncio, json, urllib.request, websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        js = """
        (() => {
            const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map(i => ({
                id: i.id,
                className: i.className,
                accept: i.accept
            }));
            const buttons = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean);
            const textNodes = Array.from(document.querySelectorAll('.asset-panel, .media-panel, [class*="upload"], [class*="asset"]'))
                                .map(el => el.innerText ? el.innerText.slice(0, 100) : '')
                                .filter(Boolean);
            return { fileInputs, buttons: buttons.slice(0, 20), textNodes: textNodes.slice(0, 5) };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print(json.dumps(msg['result']['result']['value'], indent=2))
                break

asyncio.run(check())
