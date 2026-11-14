import asyncio
import json
import urllib.request
import websockets

async def check_settings():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        # Click the tune / settings button
        click_tune = """
        (() => {
            const btn = document.querySelector('button[aria-label="Einstellungen"], button.settings-trigger-button');
            if (btn) {
                btn.click();
                return { success: true, aria: btn.getAttribute('aria-label') };
            }
            return { error: 'Settings button not found' };
        })()
        """
        cid = 115
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": click_tune, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        print("Tune click result:", json.loads(raw).get("result", {}).get("result", {}).get("value"))

        await asyncio.sleep(1.5)

        # Inspect opened dialog / menu / popover
        inspect_dialog = """
        (() => {
            const dialogs = Array.from(document.querySelectorAll('.mat-mdc-menu-panel, .mat-mdc-dialog-container, [role="dialog"], [role="menu"]'));
            const textContent = dialogs.map(d => (d.innerText || '').slice(0, 300));
            const options = Array.from(document.querySelectorAll('[role="option"], [role="menuitem"], mat-radio-button, mat-select, .settings-row, button'))
                .filter(el => {
                    const t = (el.innerText || '').toLowerCase();
                    return t.includes('veo') || t.includes('omni') || t.includes('flash') || t.includes('quality') || t.includes('fast') || t.includes('modell');
                })
                .map(el => ({
                    tag: el.tagName,
                    text: el.innerText.trim(),
                    aria: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    checked: el.getAttribute('aria-checked') || el.classList.contains('active') || el.classList.contains('mat-mdc-radio-checked')
                }));

            return {
                dialogsCount: dialogs.length,
                dialogsText: textContent,
                options
            };
        })()
        """
        cid2 = 116
        await ws.send(json.dumps({"id": cid2, "method": "Runtime.evaluate", "params": {"expression": inspect_dialog, "returnByValue": True}}))
        raw2 = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw2).get("result", {}).get("result", {}).get("value")
        print("Settings dialog contents:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_settings())
