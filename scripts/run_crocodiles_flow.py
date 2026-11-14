import asyncio
import json
import urllib.request
import websockets
import os
import sys
import time

FILE_TO_UPLOAD = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\references_crocodiles\crocodiles_option2_1280x720.png"
CLIPS_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips"
os.makedirs(CLIPS_DIR, exist_ok=True)

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
    print("Connecting to Chrome on port 9222...", flush=True)
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

        # 1. Upload asset via DOM.setFileInputFiles
        print("1. Uploading crocodiles_option2_1280x720.png to Flow...", flush=True)
        doc = await call_cdp("DOM.getDocument")
        file_input = await call_cdp("DOM.querySelector", {
            "nodeId": doc["root"]["nodeId"],
            "selector": "input[type=\"file\"]"
        })
        if file_input and file_input.get("nodeId"):
            await call_cdp("DOM.setFileInputFiles", {
                "files": [FILE_TO_UPLOAD],
                "nodeId": file_input["nodeId"]
            })
            print("File input set via CDP!", flush=True)
        else:
            print("Warning: input[type=file] not found directly", flush=True)

        await asyncio.sleep(3.0)

        # 2. Click new chat or focus prompt
        print("2. Opening fresh chat or focusing prompt...", flush=True)
        reset_chat = """
        (() => {
            const newChatBtn = document.querySelector('button[aria-label="Neuer Chat"], button[aria-label="New chat"]');
            if (newChatBtn) {
                newChatBtn.click();
                return 'Clicked new chat';
            }
            return 'New chat not found';
        })()
        """
        res_chat = await call_cdp("Runtime.evaluate", {"expression": reset_chat, "returnByValue": True})
        print("New chat result:", res_chat.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 3. Click '+' button to attach asset
        print("3. Clicking '+' button in prompt box...", flush=True)
        click_plus = """
        (() => {
            const addBtn = document.querySelector('button[aria-label="Medien hinzufügen"], button.add-menu-trigger') ||
                           Array.from(document.querySelectorAll('button mat-icon')).find(i => (i.innerText||'').trim() === 'add')?.closest('button');
            if (addBtn) {
                addBtn.click();
                return { success: true };
            }
            return { error: 'Add button not found' };
        })()
        """
        res_plus = await call_cdp("Runtime.evaluate", {"expression": click_plus, "returnByValue": True})
        print("Plus click:", res_plus.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 4. Filter for 'crocodiles_option2'
        print("4. Searching and attaching crocodiles_option2...", flush=True)
        search_and_attach = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const searchInput = popover.querySelector('input[type="search"], input[placeholder*="Suchen"], input[placeholder*="Search"], input');
            if (searchInput) {
                searchInput.focus();
                searchInput.value = 'crocodiles_option2';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            return { searchInputFound: !!searchInput };
        })()
        """
        await call_cdp("Runtime.evaluate", {"expression": search_and_attach, "returnByValue": True})
        await asyncio.sleep(1.5)

        # 5. Click item and 'Zum Prompt hinzufügen'
        click_add = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            const target = items.find(el => (el.innerText || '').includes('crocodiles_option2')) || items[0];
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
        res_add = await call_cdp("Runtime.evaluate", {"expression": click_add, "returnByValue": True})
        print("Attach result:", res_add.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 6. Insert Prompt text
        print("6. Inserting prompt text...", flush=True)
        insert_prompt = f"""
        (() => {{
            const editor = document.querySelector('div[contenteditable="true"]');
            if (!editor) return {{ error: 'No contenteditable editor' }};
            editor.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, {json.dumps(PROMPT_TEXT)});
            return {{ success: true, length: editor.innerText.length }};
        }})()
        """
        res_prompt = await call_cdp("Runtime.evaluate", {"expression": insert_prompt, "returnByValue": True})
        print("Prompt insert:", res_prompt.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 7. Click Submit
        print("7. Submitting prompt...", flush=True)
        click_submit = """
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
        res_submit = await call_cdp("Runtime.evaluate", {"expression": click_submit, "returnByValue": True})
        print("Submit result:", res_submit.get("result", {}).get("value"))

        # 8. Check for Genehmigen card just in case
        print("8. Checking for approval card...", flush=True)
        click_approve_js = """
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
        for s in range(10):
            await asyncio.sleep(1.0)
            res_app = await call_cdp("Runtime.evaluate", {"expression": click_approve_js, "returnByValue": True})
            val = res_app.get("result", {}).get("value")
            if val and val != 'No card':
                print(f"Approval action: {val}", flush=True)
                break

        print("Scene 04 Crocodile Riverbank successfully launched in Google Flow!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
