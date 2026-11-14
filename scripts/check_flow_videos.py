import asyncio
import json
import urllib.request
import websockets

async def check_videos():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            // Find all video cards or elements in the page
            const allVideos = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src || v.currentSrc,
                duration: v.duration,
                paused: v.paused,
                parentElementClass: v.parentElement ? v.parentElement.className : ''
            }));

            // Find any generating or pending cards
            const cards = Array.from(document.querySelectorAll('[class*="asset"], [class*="card"], [class*="node"], [class*="item"]'))
                .filter(el => {
                    const t = (el.innerText || '').toLowerCase();
                    return t.includes('serpent') || t.includes('snake') || t.includes('sandstone') || t.includes('%') || t.includes('generier');
                })
                .map(el => ({
                    className: el.className,
                    text: (el.innerText || '').slice(0, 150)
                }));

            return {
                allVideos,
                cards: cards.slice(-5)
            };
        })()
        """
        cid = 104
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Videos & Cards:", json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_videos())
