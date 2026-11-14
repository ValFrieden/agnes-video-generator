import asyncio
import json
import urllib.request
import websockets
import base64
import time

async def click_videos_and_snap():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        async def call_cdp(method, params=None):
            cid = int(time.time() * 1000) % 1000000
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == cid:
                    return msg.get("result", {})

        # Click on Videos at (90, 205)
        print("Clicking Videos menu item at x=90, y=205...")
        await call_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 90, "y": 205, "button": "left", "clickCount": 1})
        await call_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 90, "y": 205, "button": "left", "clickCount": 1})
        
        await asyncio.sleep(2.0)
        
        # Capture screenshot
        await call_cdp("Page.enable")
        snap = await call_cdp("Page.captureScreenshot")
        with open("live_flow_check.png", "wb") as f:
            f.write(base64.b64decode(snap["data"]))
        print("Updated screenshot saved to live_flow_check.png")

asyncio.run(click_videos_and_snap())
