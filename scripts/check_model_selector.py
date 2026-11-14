import asyncio
import json
import urllib.request
import websockets

async def check_model_selector():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            // Find all elements in prompt box
            const box = document.querySelector('.agent-panel-prompt-box, [class*="prompt-box"]') || document.body;
            const buttons = Array.from(box.querySelectorAll('button, div[role="button"], mat-select, [class*="model"]'))
                .map(b => ({
                    tag: b.tagName,
                    text: b.innerText.trim(),
                    aria: b.getAttribute('aria-label'),
                    className: b.className
                }));

            // Check if there is an active chip attached in the editor
            const chips = Array.from(box.querySelectorAll('.chip, [class*="chip"], mat-chip')).map(c => c.innerText.trim());

            return {
                buttons,
                chips
            };
        })()
        """
        cid = 121
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Prompt box elements:", json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_model_selector())
