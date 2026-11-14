import asyncio
import json
import urllib.request
import websockets

async def inspect_chat_deep():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            // Find all agent-panel or chat messages
            const messages = Array.from(document.querySelectorAll('.agent-panel-history *'))
                .filter(el => el.children.length === 0 && (el.innerText || '').trim().length > 0)
                .map(el => (el.innerText || '').trim());
            
            // Get unique messages from the bottom
            const unique = [];
            for (let i = messages.length - 1; i >= 0; i--) {
                const m = messages[i];
                if (!unique.includes(m)) {
                    unique.unshift(m);
                }
                if (unique.length > 30) break;
            }

            // Check if there are canvas nodes or timeline items
            const canvasNodes = Array.from(document.querySelectorAll('.canvas-node, .media-card, .asset-card, [data-node-id]')).map(n => ({
                id: n.getAttribute('data-node-id'),
                text: (n.innerText || '').slice(0, 100),
                hasVideo: !!n.querySelector('video'),
                videoSrc: n.querySelector('video') ? n.querySelector('video').src : null
            }));

            // Check if any error or toast message exists
            const toasts = Array.from(document.querySelectorAll('simple-snack-bar, mat-snack-bar-container, .toast, .error-message')).map(t => t.innerText);

            return {
                recentMessages: unique,
                canvasNodesCount: canvasNodes.length,
                canvasNodes: canvasNodes.slice(-5),
                toasts
            };
        })()
        """
        cid = 105
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Deep Chat Inspection:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(inspect_chat_deep())
