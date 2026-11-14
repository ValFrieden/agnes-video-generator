import asyncio
import json
import urllib.request
import websockets
import base64
import time

async def click_card_and_check():
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

        print("Clicking top-left card at x=250, y=250...")
        await call_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 250, "y": 250, "button": "left", "clickCount": 1})
        await call_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 250, "y": 250, "button": "left", "clickCount": 1})
        await asyncio.sleep(2.0)

        # Check current URL and open dialogs/buttons
        js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.innerText || '',
                aria: b.getAttribute('aria-label') || '',
                cls: b.className
            }));
            const videos = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src,
                duration: v.duration,
                currentSrc: v.currentSrc
            }));
            return {
                url: window.location.href,
                btnsCount: btns.length,
                downloadBtns: btns.filter(b => (b.aria + b.text).toLowerCase().includes('download') || (b.aria + b.text).toLowerCase().includes('herunterladen')),
                videos: videos
            };
        })()
        """
        res = await call_cdp("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print(res.get("result", {}).get("value"))

        await call_cdp("Page.enable")
        snap = await call_cdp("Page.captureScreenshot")
        with open("live_flow_check.png", "wb") as f:
            f.write(base64.b64decode(snap["data"]))
        print("Updated screenshot saved to live_flow_check.png")

asyncio.run(click_card_and_check())
