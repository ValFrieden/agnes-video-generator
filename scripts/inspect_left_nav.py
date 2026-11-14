import asyncio
import json
import urllib.request
import websockets

async def inspect():
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

        js = """
        (() => {
            const els = Array.from(document.querySelectorAll('*')).filter(e => {
                return (e.innerText || '').trim() === 'Videos' && e.children.length === 0;
            });
            return els.map(e => {
                const r = e.getBoundingClientRect();
                return {
                    tag: e.tagName,
                    cls: e.className,
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2,
                    w: r.width,
                    h: r.height
                };
            });
        })()
        """
        res = await call_cdp("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print("Videos elements:", res.get("result", {}).get("value"))

asyncio.run(inspect())
