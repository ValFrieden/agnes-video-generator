import asyncio
import json
import urllib.request
import websockets
import base64

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def capture():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.captureScreenshot'}))
        res = json.loads(await ws.recv())
        b64data = res['result']['data']
        with open('moy_mir_iz_snov_frames/flow_live_state.png', 'wb') as f:
            f.write(base64.b64decode(b64data))
        print("Screenshot saved to moy_mir_iz_snov_frames/flow_live_state.png")

if __name__ == '__main__':
    asyncio.run(capture())
