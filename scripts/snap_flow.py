import asyncio, json, urllib.request, websockets, base64

async def snap():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
        for _ in range(30):
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            if msg.get('id') == 1:
                img_data = base64.b64decode(msg['result']['data'])
                with open('C:/Users/Valeri/.gemini/antigravity/brain/5206faf6-a4af-482f-ad2b-3902d5efa61a/flow_live_view.png', 'wb') as f:
                    f.write(img_data)
                print("Captured flow_live_view.png successfully!")
                break

asyncio.run(snap())
