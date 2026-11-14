import asyncio
import json
import urllib.request
import websockets
import os
import sys
import time

CROCODILE_IMG = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\references_crocodiles\crocodiles_option2_1280x720.png")
print("Target file:", CROCODILE_IMG, "Exists:", os.path.exists(CROCODILE_IMG))

PROMPT_TEXT = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "CRITICAL REALISM & ANATOMY (CROCODILIAN LOCOMOTION & RIVERBANK DYNAMICS): "
    "A solitary 34-year-old athletic man seen strictly from behind (Back-to-Camera, dark graphite tactical overshirt, "
    "dark cargo pants, distressed boots with wet mud traces, textured brown hair, absolutely NO visible face) "
    "walks calmly and steadily forward across the wide muddy riverbank toward the water. "
    "REPTILIAN BIOMECHANICS & KINEMATICS: The giant wild saltwater crocodiles move with authentic heavy crocodilian locomotion. "
    "Some remain resting heavily on the wet silt with low bellies pressed to the ground, while two foreground crocodiles slowly "
    "crawl with deliberate, powerful limb movements and subtle lateral trunk flexing, sliding their massive mud-caked bodies "
    "down the slope into the dark murky river, creating gentle concentric water ripples. "
    "Their armored dorsal scutes and osteoderms catch specular morning highlights and wet mud sheen. "
    "STRICT ORGANIC ASYMMETRY: The crocodiles are positioned at completely irregular depths, asymmetrical angles, and distances, "
    "reacting to the environment with natural asynchronous timing, zero mirrored choreography. "
    "CINEMATOGRAPHY & LIGHTING: Smooth low-angle tracking camera following directly behind the man at waist height, moving forward at a steady walking pace. "
    "Golden morning sunlight cuts through dense tropical river mist, casting soft elongated shadows and rim-lighting the wet mud flats. "
    "Photorealistic 35mm film texture, ARRI Alexa optical look, authentic wildlife documentary cinematography, anti-slop, zero CGI distortion."
)

async def main():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
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

        # Step 1: Enable domains
        await call_cdp("Page.enable")
        await call_cdp("DOM.enable")
        await call_cdp("Page.setInterceptFileChooserDialog", {"enabled": True})

        # Step 2: Click Menü „Medien hinzufügen“ button in header
        print("Clicking 'Menü Medien hinzufügen'...", flush=True)
        click_add_menu = """
        (() => {
            const btn = document.querySelector('button[aria-label*="Medien hinzufügen"], button[aria-label*="hinzufügen"]');
            if (btn) {
                btn.click();
                return { success: true, aria: btn.getAttribute('aria-label') };
            }
            return { error: 'Not found' };
        })()
        """
        res_menu = await call_cdp("Runtime.evaluate", {"expression": click_add_menu, "returnByValue": True})
        print("Add menu click:", res_menu.get("result", {}).get("value"))

        await asyncio.sleep(1.0)

        # Step 3: In the opened menu, click 'Dateien hochladen' or 'Hochladen'
        click_upload_item = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button'));
            const uploadItem = items.find(i => {
                const t = (i.innerText || '').toLowerCase();
                return t.includes('hochladen') || t.includes('upload') || t.includes('datei');
            });
            if (uploadItem) {
                uploadItem.click();
                return { success: true, text: uploadItem.innerText };
            }
            return { error: 'Upload item not found', available: items.map(i => i.innerText.trim()).filter(Boolean) };
        })()
        """
        res_up = await call_cdp("Runtime.evaluate", {"expression": click_upload_item, "returnByValue": True})
        print("Upload item click:", res_up.get("result", {}).get("value"))

        # Step 4: Intercept file chooser dialog
        print("Waiting for fileChooserOpened event...", flush=True)
        file_chosen = False
        for _ in range(15):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
                msg = json.loads(raw)
                if msg.get("method") == "Page.fileChooserOpened":
                    print("fileChooserOpened intercepted!", flush=True)
                    backend_node_id = msg["params"].get("backendNodeId")
                    set_files = {
                        "files": [CROCODILE_IMG]
                    }
                    if backend_node_id:
                        set_files["backendNodeId"] = backend_node_id
                    await call_cdp("DOM.setFileInputFiles", set_files)
                    print("DOM.setFileInputFiles sent!", flush=True)
                    file_chosen = True
                    break
            except asyncio.TimeoutError:
                pass

        if not file_chosen:
            print("Trying fallback: looking for input[type=file] directly...", flush=True)
            doc = await call_cdp("DOM.getDocument")
            file_input = await call_cdp("DOM.querySelector", {
                "nodeId": doc["root"]["nodeId"],
                "selector": "input[type=\"file\"]"
            })
            if file_input and file_input.get("nodeId"):
                await call_cdp("DOM.setFileInputFiles", {
                    "files": [CROCODILE_IMG],
                    "nodeId": file_input["nodeId"]
                })
                print("Fallback DOM.setFileInputFiles succeeded!", flush=True)

        print("Waiting 5s for upload to register...", flush=True)
        await asyncio.sleep(5.0)

        # Step 5: Start a new chat session
        print("Starting new chat session...", flush=True)
        new_chat_js = """
        (() => {
            const btn = document.querySelector('button[aria-label="Neue Sitzung beginnen"], button[aria-label="New chat"]');
            if (btn) {
                btn.click();
                return 'Clicked Neue Sitzung beginnen';
            }
            return 'New chat btn not found';
        })()
        """
        res_nc = await call_cdp("Runtime.evaluate", {"expression": new_chat_js, "returnByValue": True})
        print("New chat result:", res_nc.get("result", {}).get("value"))
        await asyncio.sleep(2.0)

        # Step 6: Click '+' in prompt box
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
        print("Prompt plus click:", res_pp.get("result", {}).get("value"))
        await asyncio.sleep(2.0)

        # Step 7: Filter and select crocodiles_option2
        print("Selecting crocodiles_option2...", flush=True)
        select_asset_js = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const searchInput = popover.querySelector('input[type="search"], input[placeholder*="Suchen"], input[placeholder*="Search"], input');
            if (searchInput) {
                searchInput.focus();
                searchInput.value = 'crocodiles';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            return { searchInputFound: !!searchInput };
        })()
        """
        await call_cdp("Runtime.evaluate", {"expression": select_asset_js, "returnByValue": True})
        await asyncio.sleep(1.5)

        # Step 8: Click target asset and 'Zum Prompt hinzufügen'
        attach_asset_js = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            const target = items.find(el => (el.innerText || '').includes('crocodiles')) || items[0];
            if (target) {
                target.click();
            }
            const addBtn = Array.from(popover.querySelectorAll('button')).find(b => {
                const t = (b.innerText || '').toLowerCase();
                return t.includes('prompt hinzuf') || t.includes('hinzufügen') || t.includes('add');
            });
            if (addBtn) {
                addBtn.click();
                return { success: true, target: target ? target.innerText.slice(0, 30) : 'none' };
            }
            return { error: 'Add btn not found', targetFound: !!target };
        })()
        """
        res_attach = await call_cdp("Runtime.evaluate", {"expression": attach_asset_js, "returnByValue": True})
        print("Attach result:", res_attach.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # Step 9: Insert prompt text
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

        # Step 10: Submit
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

        # Step 11: Auto-approve
        print("Monitoring for approval card...", flush=True)
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

        print("\n>>> Scene 04 launch pipeline complete! <<<", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
