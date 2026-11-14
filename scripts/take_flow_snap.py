import asyncio
import json
import urllib.request
import websockets
import base64

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.captureScreenshot'}))
        res = json.loads(await ws.recv())
        with open('live_flow_check.png', 'wb') as f:
            f.write(base64.b64decode(res['result']['data']))
        print('Screenshot saved: live_flow_check.png')

if __name__ == '__main__':
    asyncio.run(check())
