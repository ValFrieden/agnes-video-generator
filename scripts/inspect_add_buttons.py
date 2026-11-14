import asyncio, json, urllib.request, websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        js = """
        (() => {
            const addButtons = Array.from(document.querySelectorAll('button, div[role="button"]')).filter(b => {
                const txt = b.innerText || '';
                const aria = b.getAttribute('aria-label') || '';
                return txt.includes('add') || aria.includes('add') || aria.includes('Upload') || txt.includes('Upload');
            }).map(b => ({
                tag: b.tagName,
                text: b.innerText,
                aria: b.getAttribute('aria-label'),
                className: b.className,
                rect: b.getBoundingClientRect()
            }));
            return addButtons;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print(json.dumps(msg['result']['result']['value'], indent=2))
                break

asyncio.run(check())
