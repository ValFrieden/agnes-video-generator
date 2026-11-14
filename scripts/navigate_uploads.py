import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        click_js = """
        (() => {
            const items = Array.from(document.querySelectorAll('mat-list-item, button, [role="listitem"], div')).filter(el => (el.innerText || '').trim() === 'Uploads');
            if (items.length > 0) {
                items[0].click();
                return 'Clicked Uploads';
            }
            return 'Not found';
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": click_js, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print("Uploads click result:", res["result"]["result"]["value"])
        await asyncio.sleep(1.5)

if __name__ == "__main__":
    asyncio.run(main())
