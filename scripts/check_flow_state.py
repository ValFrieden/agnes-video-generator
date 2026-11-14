import asyncio, json, websockets

async def check_flow():
    url = "ws://localhost:9222/devtools/page/BCF5D7817C7B8B9941C6D92B34C8A486"
    async with websockets.connect(url, max_size=20*1024*1024) as ws:
        js = """
        (() => {
            return {
                url: location.href,
                title: document.title,
                buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean).slice(0, 15),
                inputs: Array.from(document.querySelectorAll('input[type="file"]')).length
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print(json.dumps(msg['result']['result']['value'], indent=2))
                break

asyncio.run(check_flow())
