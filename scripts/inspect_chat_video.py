import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        inspect_js = """
        (() => {
            const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src,
                currentSrc: v.currentSrc,
                duration: v.duration,
                paused: v.paused,
                rect: v.getBoundingClientRect()
            }));
            const chatVidBtns = Array.from(document.querySelectorAll('.agent-message button, .chat-message button, [role="article"] button')).map(b => ({
                text: b.innerText,
                aria: b.getAttribute('aria-label')
            }));
            return { vids, chatVidBtns };
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": inspect_js, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res["result"]["result"]["value"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
