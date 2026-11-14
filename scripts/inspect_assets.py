import asyncio, json, websockets

async def check_assets():
    url = "ws://localhost:9222/devtools/page/BCF5D7817C7B8B9941C6D92B34C8A486"
    async with websockets.connect(url, max_size=20*1024*1024) as ws:
        js = """
        (() => {
            const assets = Array.from(document.querySelectorAll('img')).map(img => ({
                src: img.src,
                alt: img.alt,
                className: img.className
            }));
            const buttons = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean);
            return { totalImgs: assets.length, sampleImgs: assets.slice(0, 10), buttons: buttons.slice(0, 20) };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print(json.dumps(msg['result']['result']['value'], indent=2))
                break

asyncio.run(check_assets())
