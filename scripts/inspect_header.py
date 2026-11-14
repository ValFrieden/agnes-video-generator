import asyncio
import json
import urllib.request
import websockets

async def inspect_header():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, [role="button"]')).map(b => ({
                text: (b.innerText || '').trim(),
                aria: b.getAttribute('aria-label'),
                rect: b.getBoundingClientRect()
            })).filter(b => b.rect.y < 80);
            return btns;
        })()
        """
        cid = 112
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Header buttons:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(inspect_header())
