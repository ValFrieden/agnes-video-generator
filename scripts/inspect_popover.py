import asyncio, json, urllib.request, websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        js = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container');
            if (!popover) return { error: 'No .add-menu-popover-container found' };
            const allElements = Array.from(popover.querySelectorAll('*')).map(el => ({
                tag: el.tagName,
                className: el.className,
                text: el.innerText ? el.innerText.trim().slice(0, 50) : '',
                aria: el.getAttribute('aria-label')
            })).filter(x => x.text || x.aria);
            return { count: allElements.length, items: allElements.slice(0, 25) };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print(json.dumps(msg['result']['result']['value'], indent=2))
                break

asyncio.run(check())
