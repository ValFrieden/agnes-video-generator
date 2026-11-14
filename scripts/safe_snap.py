import asyncio
import json
import urllib.request
import websockets
import base64

async def safe_snap():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        req_id = 999
        await ws.send(json.dumps({'id': req_id, 'method': 'Page.captureScreenshot'}))
        
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            if msg.get('id') == req_id:
                data = msg['result']['data']
                with open('live_flow_check.png', 'wb') as f:
                    f.write(base64.b64decode(data))
                print('Screenshot successfully saved: live_flow_check.png')
                break

if __name__ == '__main__':
    asyncio.run(safe_snap())
