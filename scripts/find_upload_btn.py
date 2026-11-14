import asyncio, json, urllib.request, websockets

async def check_upload():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Check all buttons with text or aria or icons
        js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, div[role="button"]')).map(b => ({
                text: b.innerText.trim(),
                aria: b.getAttribute('aria-label'),
                className: b.className
            }));
            const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map(i => ({
                id: i.id,
                name: i.name,
                accept: i.accept
            }));
            return { buttons: btns.filter(b => b.text.includes('Upload') || b.text.includes('add') || b.text.includes('Hinzufügen') || (b.aria && b.aria.includes('upload'))), fileInputs };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print(json.dumps(msg['result']['result']['value'], indent=2))
                break

asyncio.run(check_upload())
