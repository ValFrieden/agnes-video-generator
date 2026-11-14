import asyncio
import json
import urllib.request
import websockets

async def check_and_click():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        # First click 'Zum Prompt hinzufügen'
        click_add = """
        (() => {
            const addBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('Zum Prompt hinzuf'));
            let addClicked = false;
            if (addBtn) {
                addBtn.click();
                addClicked = true;
            }

            // Also check all buttons in the right chat area
            const chatButtons = Array.from(document.querySelectorAll('.agent-panel-history button, .agent-chat-messages button, div.option-row'))
                .map(b => ({
                    text: b.innerText.trim(),
                    aria: b.getAttribute('aria-label')
                }));

            // Check full text of last chat message
            const body = document.body.innerText;
            const idx = body.indexOf('requires 100 credits');
            const snippet = idx !== -1 ? body.slice(idx - 50, idx + 400) : 'not found';

            return {
                addClicked,
                chatButtons,
                snippet
            };
        })()
        """
        cid = 120
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": click_add, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Result:", json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_and_click())
