import asyncio
import json
import urllib.request
import websockets

async def check_settings_trigger():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        # First close previous menu
        await ws.send(json.dumps({'id': 1, 'method': 'Input.dispatchKeyEvent', 'params': {'type': 'keyDown', 'key': 'Escape'}}))
        await ws.recv()
        await asyncio.sleep(0.5)

        # Click button.settings-trigger-button
        click_pill = """
        (() => {
            const btn = document.querySelector('button.settings-trigger-button');
            if (btn) {
                btn.click();
                return { success: true, text: btn.innerText, aria: btn.getAttribute('aria-label'), html: btn.outerHTML };
            }
            return { error: 'settings-trigger-button not found' };
        })()
        """
        cid = 117
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": click_pill, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Pill click result:", json.dumps(res, indent=2))

        await asyncio.sleep(1.5)

        # Inspect opened dialog/menu
        inspect_dialog = """
        (() => {
            const dialogs = Array.from(document.querySelectorAll('.mat-mdc-menu-panel, .mat-mdc-dialog-container, [role="dialog"], [role="menu"]'));
            const textContent = dialogs.map(d => (d.innerText || '').slice(0, 500));
            const allItems = Array.from(document.querySelectorAll('[role="option"], [role="menuitem"], mat-radio-button, mat-select, button'))
                .map(el => (el.innerText || '').trim())
                .filter(t => t.includes('Veo') || t.includes('Omni') || t.includes('Modell') || t.includes('Model') || t.includes('Flash') || t.includes('Quality') || t.includes('Fast'));

            return {
                dialogsText: textContent,
                modelItems: allItems
            };
        })()
        """
        cid2 = 118
        await ws.send(json.dumps({"id": cid2, "method": "Runtime.evaluate", "params": {"expression": inspect_dialog, "returnByValue": True}}))
        raw2 = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res2 = json.loads(raw2).get("result", {}).get("result", {}).get("value")
        print("Model dialog result:", json.dumps(res2, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_settings_trigger())
