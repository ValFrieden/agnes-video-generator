import asyncio
import json
import urllib.request
import websockets

async def check_grid():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        async def call_cdp(method, params=None):
            cid = 1
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == cid:
                    return msg.get("result", {})

        # Find elements at coordinates x=250, y=250 (top left card in grid)
        js = """
        (() => {
            const el1 = document.elementFromPoint(250, 250);
            const el2 = document.elementFromPoint(600, 250);
            function getInfo(el) {
                if (!el) return null;
                return {
                    tag: el.tagName,
                    cls: el.className,
                    parentTag: el.parentElement ? el.parentElement.tagName : null,
                    parentCls: el.parentElement ? el.parentElement.className : null,
                    text: el.innerText || ''
                };
            }
            return {
                card1: getInfo(el1),
                card2: getInfo(el2)
            };
        })()
        """
        res = await call_cdp("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print(res.get("result", {}).get("value"))

asyncio.run(check_grid())
