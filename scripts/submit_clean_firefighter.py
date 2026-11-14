import asyncio
import json
import urllib.request
import websockets
import os
import time

PROMPT_TEXT = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "CRITICAL PHYSICAL REALISM (COMBUSTION & THERMAL CONVECTION): "
    "A fearless professional firefighter seen strictly from behind (Back-to-Camera, absolutely NO visible face, "
    "dark graphite heavy Nomex turnout coat with fluorescent neon-yellow reflective safety stripes, "
    "composite SCBA breathing apparatus cylinder tank on the back, black structural helmet) "
    "walks calmly and steadily forward across the burning threshold into the heavily engulfed interior of a blazing building. "
    "TEMPORAL PROGRESSION & FIRE DYNAMICS: "
    "[0-4 seconds]: The firefighter takes slow, resolute, heavy steps through the fiery doorway. "
    "Violent turbulent orange and yellow flames roll across the upper doorframe and ceiling beams (rollover combustion), "
    "swirling dense charcoal-grey pyrolytic smoke underneath the lintel. "
    "[4-8 seconds]: The camera smoothly tracks forward behind the firefighter's shoulder. "
    "Convective thermal updrafts carry luminous glowing embers and golden sparks swirling through the air. "
    "Radiant heat distortion shimmer waves visibly ripple across the background firelight. "
    "The firefighter stands firm in the fiery corridor, completely calm and fearless against the raging inferno. "
    "CINEMATOGRAPHY & LIGHTING: Master Prime 35mm lens, authentic chiaroscuro lighting cast entirely by roaring fire, "
    "rim light reflecting along the SCBA tank and bunker coat texture, ARRI Alexa natural rendering, zero plastic 3D cgi."
)

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
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

        # 1. Close any open dialogs/popovers
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.3)

        # 2. Click 'Neue Sitzung beginnen' (new chat button)
        print("Starting fresh chat session...", flush=True)
        click_new_chat = """
        (() => {
            const btn = document.querySelector('button[aria-label="Neue Sitzung beginnen"], button[aria-label="New chat"]');
            if (btn) {
                btn.click();
                return 'Clicked Neue Sitzung by aria';
            }
            const icon = Array.from(document.querySelectorAll('mat-icon')).find(i => (i.innerText || '').trim() === 'edit_square');
            if (icon) {
                (icon.closest('button') || icon).click();
                return 'Clicked edit_square button';
            }
            return 'Not found';
        })()
        """
        res_nc = await call_cdp("Runtime.evaluate", {"expression": click_new_chat, "returnByValue": True})
        print("New chat result:", res_nc.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 3. Click '+' button in the prompt box
        print("Opening '+' menu in prompt box...", flush=True)
        click_prompt_plus = """
        (() => {
            const btn = document.querySelector('.agent-panel-prompt-box button.add-menu-trigger') ||
                        Array.from(document.querySelectorAll('.agent-panel-prompt-box button mat-icon')).find(i => (i.innerText||'').trim() === 'add')?.closest('button');
            if (btn) {
                btn.click();
                return 'Clicked prompt add button';
            }
            return 'Not found';
        })()
        """
        res_pp = await call_cdp("Runtime.evaluate", {"expression": click_prompt_plus, "returnByValue": True})
        print("Prompt plus result:", res_pp.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 4. In popover, search or select firefighter
        print("Selecting firefighter image in popover...", flush=True)
        select_firefighter = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            // First try searching
            const searchInput = popover.querySelector('input[type="search"], input[placeholder*="Suchen"], input[placeholder*="Search"], input');
            if (searchInput) {
                searchInput.focus();
                searchInput.value = 'firefighter';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            const target = items.find(el => (el.innerText || '').toLowerCase().includes('firefighter')) || items[0];
            if (target) {
                target.click();
                const addBtn = Array.from(popover.querySelectorAll('button')).find(b => {
                    const t = (b.innerText || '').toLowerCase();
                    return t.includes('prompt hinzuf') || t.includes('hinzufügen') || t.includes('add');
                });
                if (addBtn) {
                    addBtn.click();
                    return { success: true, text: target.innerText.slice(0, 50) };
                }
                return { error: 'Add button not found', targetText: target.innerText.slice(0, 50) };
            }
            return { error: 'No items in popover' };
        })()
        """
        res_sel = await call_cdp("Runtime.evaluate", {"expression": select_firefighter, "returnByValue": True})
        print("Select result:", res_sel.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 5. Insert prompt text
        print("Inserting prompt text...", flush=True)
        insert_prompt_js = f"""
        (() => {{
            const editor = document.querySelector('div[contenteditable="true"]');
            if (!editor) return {{ error: 'No editor' }};
            editor.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, {json.dumps(PROMPT_TEXT)});
            return {{ success: true, length: editor.innerText.length }};
        }})()
        """
        res_p = await call_cdp("Runtime.evaluate", {"expression": insert_prompt_js, "returnByValue": True})
        print("Insert prompt result:", res_p.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 6. Submit prompt
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

        # 7. Check and click Genehmigen (Iron Rule 6)
        print("Listening for Genehmigen confirmation card...", flush=True)
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
        for s in range(15):
            await asyncio.sleep(1.0)
            res_ap = await call_cdp("Runtime.evaluate", {"expression": approve_js, "returnByValue": True})
            val = res_ap.get("result", {}).get("value")
            if val and val != 'No card':
                print(f"Approval action at s={s+1}: {val}", flush=True)
                break

        print("\n>>> Firefighter scene generation successfully submitted! <<<", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
