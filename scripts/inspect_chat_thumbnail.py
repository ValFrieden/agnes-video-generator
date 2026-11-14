import asyncio
import json
import urllib.request
import websockets

async def inspect_chat_thumbnail():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            // Find all images or video elements inside the chat sidebar (right panel)
            // The right panel usually has an agent or side-panel class
            const rightPanel = document.querySelector('aside, [class*="agent-panel"], [class*="side-panel"], [class*="chat"]') || document.body;
            
            // Find elements with play icon or thumbnails in chat
            const mediaInChat = Array.from(document.querySelectorAll('img, video')).filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.left > window.innerWidth * 0.5; // in right half of screen
            }).map(el => ({
                tag: el.tagName,
                src: el.src,
                currentSrc: el.currentSrc,
                rect: { x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y, w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height },
                parentText: (el.parentElement ? el.parentElement.innerText : '').slice(0, 100),
                parentHTML: el.parentElement ? el.parentElement.outerHTML.slice(0, 300) : ''
            }));

            // Also check all clickable elements near that thumbnail
            return {
                mediaInChat
            };
        })()
        """
        cid = 107
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Media in right panel:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(inspect_chat_thumbnail())
