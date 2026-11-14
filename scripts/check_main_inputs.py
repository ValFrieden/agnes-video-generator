import asyncio
import json
import urllib.request
import websockets

async def check_main_inputs():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const inputs = Array.from(document.querySelectorAll('input[type="file"]')).map(i => ({
                id: i.id,
                className: i.className,
                accept: i.accept
            }));
            const uploadTab = Array.from(document.querySelectorAll('button, a, div[role="button"]'))
                .find(el => (el.innerText || '').trim() === 'Uploads');
            
            return {
                inputs,
                uploadTabFound: !!uploadTab
            };
        })()
        """
        cid = 111
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Inputs on main page:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(check_main_inputs())
