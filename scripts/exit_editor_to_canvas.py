import asyncio
import json
import urllib.request
import websockets

async def exit_editor():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            // First close any open modal/dialog by clicking escape or close button or outside
            const closeBtn = document.querySelector('button[aria-label="Schließen"], button[aria-label="Close"]');
            if (closeBtn) closeBtn.click();

            // Click 'Fertig' or back arrow
            const fertigBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').trim() === 'Fertig');
            if (fertigBtn) {
                fertigBtn.click();
                return 'Clicked Fertig';
            }
            const backBtn = document.querySelector('button[aria-label="Zurück"], button[aria-label="Back"]');
            if (backBtn) {
                backBtn.click();
                return 'Clicked Back arrow';
            }
            return 'Neither Fertig nor Back found';
        })()
        """
        cid = 110
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Exit editor result:", res)

if __name__ == "__main__":
    asyncio.run(exit_editor())
