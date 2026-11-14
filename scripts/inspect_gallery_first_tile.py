import asyncio
import json
import urllib.request
import websockets

async def check_first_tile():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            // Find all cards in the main gallery
            const cards = Array.from(document.querySelectorAll('.asset-card, .gallery-item, .media-card, [class*="card"], [class*="asset"]'))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.x > 100 && rect.x < 1000 && rect.y > 100 && rect.width > 200;
                });

            // Find first tile
            const first = cards[0];
            const buttons = first ? Array.from(first.querySelectorAll('button')).map(b => ({
                text: b.innerText,
                aria: b.getAttribute('aria-label')
            })) : [];

            // Also check the error card in chat to see why it failed
            const errorCards = Array.from(document.querySelectorAll('.error-card, [class*="error"], [class*="fail"]'))
                .map(e => e.innerText.slice(0, 200));

            return {
                cardsCount: cards.length,
                firstButtons: buttons,
                firstRect: first ? first.getBoundingClientRect() : null,
                errorCards
            };
        })()
        """
        cid = 119
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("First tile info:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(check_first_tile())
