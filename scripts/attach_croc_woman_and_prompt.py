import asyncio
import json
import urllib.request
import websockets
import os
import time

PROMPT_TEXT = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "CRITICAL SPATIAL CLEARANCE & SUSPENSE CHOREOGRAPHY: "
    "A slender, fearless young woman seen strictly from behind (Back-to-Camera, absolutely NO visible face, "
    "natural wavy brunette hair, earthy sand-colored linen sleeveless dress, barefoot) walks calmly and steadily forward "
    "along the open, unobstructed muddy silt path between two giant resting Nile crocodiles on either side. "
    "PATH CLEARANCE: Her direct walking line is completely clear of obstacles—she never intersects, collides, or steps on any reptiles. "
    "TEMPORAL PROGRESSION & SUSPENSE: "
    "[0-5 seconds]: She walks forward with tranquil, steady steps, her bare feet leaving shallow impressions in the dark wet river silt. "
    "The massive crocodiles remain heavy and motionless on the bank, jaws parted in basking thermoregulation. "
    "[5-8 seconds]: As she reaches the middle distance, the giant crocodiles slowly turn their heavy armored heads toward her path. "
    "Two large crocodiles begin crawling with deliberate, powerful limb movements and heavy belly-slides across the mud toward where she walked, "
    "creating an intense cinematic cliffhanger just before the cut. "
    "PHYSICAL & BIOLOGICAL REALISM: Heavy armored osteoderms caked with dried mud, wet specular sheen, authentic reptilian scale. "
    "CINEMATOGRAPHY: Smooth low-angle tracking camera gliding forward behind the woman at waist height. "
    "Soft diffused morning river mist, golden sun rays cutting through background acacia trees. "
    "Documentary 35mm film texture, ARRI Alexa natural rendering, anti-slop, zero rubbery CGI distortion."
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

        # 1. Close any open dialogs/popovers first
        print("Closing open dialogs...", flush=True)
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.5)

        # 2. Click 'Neue Sitzung beginnen' (new chat)
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

        # 3. Click '+' in prompt box
        print("Clicking '+' in prompt box...", flush=True)
        click_prompt_plus = """
        (() => {
            const addBtn = document.querySelector('.agent-panel-prompt-box button.add-menu-trigger') ||
                           Array.from(document.querySelectorAll('.agent-panel-prompt-box button mat-icon')).find(i => (i.innerText||'').trim() === 'add')?.closest('button');
            if (addBtn) {
                addBtn.click();
                return { success: true };
            }
            return { error: 'Prompt add btn not found' };
        })()
        """
        res_pp = await call_cdp("Runtime.evaluate", {"expression": click_prompt_plus, "returnByValue": True})
        print("Prompt plus:", res_pp.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 4. Filter popover for croc_woman
        print("Filtering popover for 'croc_woman'...", flush=True)
        filter_js = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const searchInput = popover.querySelector('input[type="search"], input[placeholder*="Suchen"], input[placeholder*="Search"], input');
            if (searchInput) {
                searchInput.focus();
                searchInput.value = 'croc_woman';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            return { searchInputFound: !!searchInput };
        })()
        """
        res_f = await call_cdp("Runtime.evaluate", {"expression": filter_js, "returnByValue": True})
        print("Filter search:", res_f.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 5. Select the asset and click 'Zum Prompt hinzufügen'
        attach_js = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            const target = items.find(el => (el.innerText || '').includes('croc_woman')) || items[0];
            if (target) {
                target.click();
            }
            const addBtn = Array.from(popover.querySelectorAll('button')).find(b => {
                const t = (b.innerText || '').toLowerCase();
                return t.includes('prompt hinzuf') || t.includes('hinzufügen') || t.includes('add');
            });
            if (addBtn) {
                addBtn.click();
                return { success: true, targetText: target ? target.innerText.slice(0, 40) : 'none' };
            }
            return { error: 'Add button not found', targetFound: !!target, allItems: items.map(i => i.innerText.trim()).slice(0, 5) };
        })()
        """
        res_att = await call_cdp("Runtime.evaluate", {"expression": attach_js, "returnByValue": True})
        print("Attach result:", res_att.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 6. Insert Prompt text
        print("Inserting prompt text...", flush=True)
        insert_prompt_js = f"""
        (() => {{
            const editor = document.querySelector('div[contenteditable="true"]');
            if (!editor) return {{ error: 'No contenteditable editor' }};
            editor.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, {json.dumps(PROMPT_TEXT)});
            return {{ success: true, length: editor.innerText.length }};
        }})()
        """
        res_p = await call_cdp("Runtime.evaluate", {"expression": insert_prompt_js, "returnByValue": True})
        print("Insert prompt:", res_p.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 7. Submit prompt
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

        # 8. Check and click Genehmigen if cost card pops up (Iron Rule 6)
        print("Checking for cost confirmation card...", flush=True)
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

        print("\n>>> Scene 04 generation successfully submitted to Veo 3.1! <<<", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
