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
            const btns = Array.from(document.querySelectorAll('button'));
            const uploadNavBtn = btns.find(b => (b.innerText || '').includes('Uploads'));
            if (uploadNavBtn) {
                uploadNavBtn.click();
                return 'Clicked Uploads nav button';
            }
            return 'Uploads nav button not found';
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": click_js, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print("Result:", res["result"]["result"]["value"])
        await asyncio.sleep(2.0)

if __name__ == "__main__":
    asyncio.run(main())
