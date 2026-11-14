import asyncio
import json
import urllib.request
import websockets

async def inspect_full():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const bodyText = document.body.innerText;
            const lines = bodyText.split('\\n').map(l => l.trim()).filter(Boolean);
            // find lines related to generating or video
            return {
                lastLines: lines.slice(-40)
            };
        })()
        """
        cid = 103
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Last lines of document.body.innerText:")
        for line in res.get("lastLines", []):
            print("  ", line)

if __name__ == "__main__":
    asyncio.run(inspect_full())
