import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        top_plus = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button')).filter(b => {
                const icon = b.querySelector('mat-icon');
                return icon && (icon.innerText || '').trim() === 'add';
            });
            return btns.map(b => ({
                aria: b.getAttribute('aria-label'),
                classes: b.className,
                rect: b.getBoundingClientRect()
            }));
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": top_plus, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res["result"]["result"]["value"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
