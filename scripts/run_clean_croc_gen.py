import asyncio
import json
import urllib.request
import websockets
import time

CLEAN_PROMPT = (
    "A slender young woman with natural wavy brunette hair, wearing a simple sand-colored linen sleeveless dress, "
    "walks calmly barefoot along the muddy riverbank of a wide tropical river. "
    "Her bare feet leave shallow footprints in the wet dark silt as she moves steadily forward along an open, "
    "unobstructed path between giant basking Nile crocodiles resting on the sandbank. "
    "The massive wild crocodiles rest peacefully on the mud, their armored scutes glistening with wet river sheen. "
    "As she passes, two crocodiles slowly begin crawling across the mud toward the water. "
    "Smooth low-angle tracking camera follows directly behind the woman at waist height, moving forward at a gentle walking pace. "
    "Soft golden morning sunlight cuts through river mist and acacia trees in the distance. "
    "Photorealistic 35mm documentary cinematography, natural lighting, authentic wildlife realism, zero CGI distortion."
)

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    ws_url = flow_tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        async def call_cdp(method, params=None):
            cid = int(time.time() * 1000) % 1000000
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=6.0)
                    msg = json.loads(raw)
                    if msg.get("id") == cid:
                        return msg.get("result", {})
                except asyncio.TimeoutError:
                    return None

        # 1. Close open menus with Escape
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.5)

        # 2. Click 'Neue Sitzung beginnen'
        print("Starting fresh chat session...", flush=True)
        click_new_chat = """
        (() => {
            const btn = document.querySelector('button[aria-label="Neue Sitzung beginnen"], button[aria-label="New chat"]');
            if (btn) {
                btn.click();
                return 'Clicked Neue Sitzung';
            }
            return 'New chat btn not found';
        })()
        """
        res_nc = await call_cdp("Runtime.evaluate", {"expression": click_new_chat, "returnByValue": True})
        print("New chat:", res_nc.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 3. Click '+' button in prompt box
        print("Opening '+' add menu in prompt box...", flush=True)
        click_plus = """
        (() => {
            const addBtn = document.querySelector('.agent-panel-prompt-box button.add-menu-trigger') ||
                           Array.from(document.querySelectorAll('.agent-panel-prompt-box button mat-icon')).find(i => (i.innerText||'').trim() === 'add')?.closest('button');
            if (addBtn) {
                addBtn.click();
                return { success: true };
            }
            return { error: 'Add button not found' };
        })()
        """
        res_p = await call_cdp("Runtime.evaluate", {"expression": click_plus, "returnByValue": True})
        print("Plus click:", res_p.get("result", {}).get("value"))
        await asyncio.sleep(2.0)

        # 4. Click the very first asset in the popover (which is croc_woman_cand1!)
        print("Selecting first asset in popover...", flush=True)
        select_first = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            // The first asset item
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            if (items.length === 0) return { error: 'No items in popover' };
            const first = items[0];
            first.click();
            
            // Click 'Zum Prompt hinzufügen' button
            const addBtn = Array.from(popover.querySelectorAll('button')).find(b => {
                const t = (b.innerText || '').toLowerCase();
                return t.includes('prompt hinzuf') || t.includes('hinzufügen') || t.includes('add');
            });
            if (addBtn) {
                addBtn.click();
                return { success: true, itemText: (first.innerText || '').slice(0, 30) };
            }
            return { error: 'Add button not found', itemText: (first.innerText || '').slice(0, 30) };
        })()
        """
        res_sel = await call_cdp("Runtime.evaluate", {"expression": select_first, "returnByValue": True})
        print("Select result:", res_sel.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 5. Insert clean prompt text
        print("Inserting clean prompt text...", flush=True)
        insert_js = f"""
        (() => {{
            const editor = document.querySelector('div[contenteditable="true"]');
            if (!editor) return {{ error: 'No contenteditable editor' }};
            editor.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, {json.dumps(CLEAN_PROMPT)});
            return {{ success: true, len: editor.innerText.length }};
        }})()
        """
        res_ins = await call_cdp("Runtime.evaluate", {"expression": insert_js, "returnByValue": True})
        print("Insert prompt:", res_ins.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 6. Click Submit (Generierung starten)
        print("Submitting prompt...", flush=True)
        submit_js = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"], button[aria-label="Prompt senden"], button[aria-label="Generate"]');
            if (btn) {
                btn.click();
                return 'Clicked submit by aria';
            }
            const icons = Array.from(document.querySelectorAll('.agent-panel-prompt-box mat-icon'));
            const sendIcon = icons.find(i => ['arrow_upward', 'send', 'arrow_forward'].includes((i.innerText || '').trim()));
            if (sendIcon) {
                sendIcon.closest('button').click();
                return 'Clicked send icon';
            }
            return 'Submit not found';
        })()
        """
        res_sub = await call_cdp("Runtime.evaluate", {"expression": submit_js, "returnByValue": True})
        print("Submit result:", res_sub.get("result", {}).get("value"))

        # 7. Check for Genehmigen card and click immediately (Iron Rule 6)
        print("Checking for approval card...", flush=True)
        approve_js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, div[role="button"], .option-row'));
            const alwaysBtn = btns.find(b => (b.innerText || '').includes('Im Projekt immer genehmigen'));
            if (alwaysBtn) {
                alwaysBtn.click();
                return 'Clicked Im Projekt immer genehmigen';
            }
            const approveBtn = btns.find(b => (b.innerText || '').trim().startsWith('Genehmigen'));
            if (approveBtn) {
                approveBtn.click();
                return 'Clicked Genehmigen';
            }
            return 'No card';
        })()
        """
        for s in range(12):
            await asyncio.sleep(1.0)
            res_ap = await call_cdp("Runtime.evaluate", {"expression": approve_js, "returnByValue": True})
            val = res_ap.get("result", {}).get("value")
            if val and val != 'No card':
                print(f"Approval action at s={s+1}: {val}", flush=True)
                break

        print("\nClean generation prompt submitted successfully!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
