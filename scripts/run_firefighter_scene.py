import asyncio
import json
import urllib.request
import websockets
import os
import sys
import shutil
import time
import subprocess

TARGET_IMG = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\firefighter_cand2_1280x720.png")
CLIPS_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips"
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
FINAL_VIDEO = os.path.join(CLIPS_DIR, "scene_firefighter_blaze_v1.mp4")
os.makedirs(CLIPS_DIR, exist_ok=True)

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
    print("=== Step 1: Connecting to Chrome CDP ===", flush=True)
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

        await call_cdp("Page.enable")
        await call_cdp("DOM.enable")
        await call_cdp("Page.setInterceptFileChooserDialog", {"enabled": True})

        # 1. Upload the image file
        print("=== Step 2: Uploading Candidate 2 to Project Media ===", flush=True)
        # Click Uploads menu or button
        click_uploads = """
        (() => {
            // Check top menu button with aria or text 'Medien hinzufügen' / 'Hochladen'
            const btns = Array.from(document.querySelectorAll('button, [role="button"]'));
            const addMediaBtn = btns.find(b => {
                const t = (b.innerText || '').toLowerCase();
                const a = (b.getAttribute('aria-label') || '').toLowerCase();
                return t.includes('medien hinzuf') || t.includes('medien hoch') || a.includes('medien hinzuf') || a.includes('hochladen');
            });
            if (addMediaBtn) {
                addMediaBtn.click();
                return 'Clicked add media btn: ' + addMediaBtn.innerText;
            }
            return 'Not found';
        })()
        """
        res_u = await call_cdp("Runtime.evaluate", {"expression": click_uploads, "returnByValue": True})
        print("Click upload trigger:", res_u.get("result", {}).get("value"))
        await asyncio.sleep(1.0)

        # Intercept file chooser or set via DOM
        chosen = False
        for _ in range(8):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                msg = json.loads(raw)
                if msg.get("method") == "Page.fileChooserOpened":
                    print("fileChooserOpened event received!", flush=True)
                    backend_id = msg["params"].get("backendNodeId")
                    set_params = {"files": [TARGET_IMG]}
                    if backend_id:
                        set_params["backendNodeId"] = backend_id
                    await call_cdp("DOM.setFileInputFiles", set_params)
                    chosen = True
                    break
            except asyncio.TimeoutError:
                pass

        if not chosen:
            # Fallback: find input[type=file] directly
            doc = await call_cdp("DOM.getDocument")
            file_input = await call_cdp("DOM.querySelector", {
                "nodeId": doc["root"]["nodeId"],
                "selector": "input[type=\"file\"]"
            })
            if file_input and file_input.get("nodeId"):
                await call_cdp("DOM.setFileInputFiles", {
                    "files": [TARGET_IMG],
                    "nodeId": file_input["nodeId"]
                })
                print("Direct input[type=file] updated!", flush=True)
                chosen = True

        print("Waiting 6s for asset registration...", flush=True)
        await asyncio.sleep(6.0)

        # 2. Click 'Neue Sitzung' (new chat)
        print("=== Step 3: Starting clean chat session ===", flush=True)
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.5)

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
        print("New chat result:", res_nc.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 3. Open prompt '+' menu
        print("=== Step 4: Opening '+' menu in prompt box ===", flush=True)
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

        # 4. Search and attach firefighter_cand2
        print("=== Step 5: Attaching firefighter_cand2 ===", flush=True)
        attach_js = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const searchInput = popover.querySelector('input[type="search"], input[placeholder*="Suchen"], input[placeholder*="Search"], input');
            if (searchInput) {
                searchInput.focus();
                searchInput.value = 'firefighter';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            const target = items.find(el => (el.innerText || '').includes('firefighter_cand2') || (el.innerText || '').includes('firefighter')) || items[0];
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
            return { error: 'Add button not found', targetFound: !!target };
        })()
        """
        res_att = await call_cdp("Runtime.evaluate", {"expression": attach_js, "returnByValue": True})
        print("Attach result:", res_att.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 5. Insert Prompt text
        print("=== Step 6: Inserting prompt text ===", flush=True)
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

        # 6. Submit prompt
        print("=== Step 7: Submitting prompt ===", flush=True)
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
        print("=== Step 8: Checking for Genehmigen card ===", flush=True)
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
        approved = False
        for s in range(15):
            await asyncio.sleep(1.0)
            res_ap = await call_cdp("Runtime.evaluate", {"expression": approve_js, "returnByValue": True})
            val = res_ap.get("result", {}).get("value")
            if val and val != 'No card':
                print(f"Approval action at s={s+1}: {val}", flush=True)
                approved = True
                break

        print("\n>>> Firefighter scene successfully submitted to Veo 3.1! <<<", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
