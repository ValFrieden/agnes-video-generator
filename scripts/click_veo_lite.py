import asyncio
import json
import urllib.request
import websockets

async def click_veo_lite():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, div[role="button"], .option-row, div'));
            const liteBtn = btns.find(b => (b.innerText || '').includes('Veo 3.1 - Lite'));
            if (liteBtn) {
                (liteBtn.closest('button') || liteBtn.closest('.option-row') || liteBtn).click();
                return { success: true, text: liteBtn.innerText.trim() };
            }
            return { error: 'Lite button not found' };
        })()
        """
        cid = 122
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Click result:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(click_veo_lite())
