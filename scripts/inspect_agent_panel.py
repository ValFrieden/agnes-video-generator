import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        inspect_panel = """
        (() => {
            const panel = document.querySelector('.agent-panel, mat-sidenav[position="end"], .chat-panel') || document.body;
            const elements = Array.from(panel.querySelectorAll('*')).filter(el => {
                const tag = el.tagName.toLowerCase();
                const cls = el.className || '';
                return ['mat-icon', 'button', 'img', 'video', 'canvas'].includes(tag) || (typeof cls === 'string' && cls.includes('video'));
            }).map(el => ({
                tag: el.tagName,
                class: el.className,
                text: (el.innerText || '').slice(0, 30),
                aria: el.getAttribute('aria-label') || ''
            }));
            return elements.slice(-25);
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": inspect_panel, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res["result"]["result"]["value"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
