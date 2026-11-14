import asyncio
import json
import urllib.request
import websockets

async def check_chat():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            // Check all messages in chat history
            const messages = Array.from(document.querySelectorAll('.agent-panel-history .message-container, .agent-panel-history [class*="message"], .agent-panel-history [class*="card"]'));
            const cards = messages.map(m => {
                const text = (m.innerText || '').trim();
                const buttons = Array.from(m.querySelectorAll('button')).map(b => (b.innerText || '').trim());
                const videos = Array.from(m.querySelectorAll('video')).map(v => v.src);
                return { text: text.slice(0, 300), buttons, videos };
            });

            // Also check if there is an active loading bar or spinner
            const spinners = Array.from(document.querySelectorAll('mat-progress-spinner, mat-progress-bar, [role="progressbar"], .loading-indicator')).length;

            // Also check all buttons currently on the page
            const visibleButtons = Array.from(document.querySelectorAll('button'))
                .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim())
                .filter(Boolean);

            return {
                cardsCount: cards.length,
                lastCards: cards.slice(-4),
                spinners,
                visibleButtons: visibleButtons.slice(-15)
            };
        })()
        """
        cid = 102
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Chat status:", json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_chat())
