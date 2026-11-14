import asyncio
import json
import urllib.request
import websockets
import os
import shutil
import subprocess
import time
from PIL import Image

TARGET_IMG = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\towering_wave_cand1_1280x720.png")
CLIPS_DIR = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips")
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
FINAL_VIDEO_NAME = "scene_towering_wave_v1.mp4"
FINAL_VIDEO_PATH = os.path.join(CLIPS_DIR, FINAL_VIDEO_NAME)

os.makedirs(CLIPS_DIR, exist_ok=True)

PROMPT_TEXT = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "CRITICAL PHYSICAL REALISM & FLUID DYNAMICS (COLOSSAL 5-METER BREAKING WAVE): "
    "A fearless barefoot young woman seen strictly from behind (Back-to-Camera, 100% NO visible face, flowing emerald green silk dress, long dark hair windswept by coastal gale) "
    "stands poised and immovable upon wet dark basalt shoreline rocks facing a colossal 5-meter ocean wave. "
    "TEMPORAL PROGRESSION & WATER MASS DYNAMICS: "
    "[0-4 seconds]: The camera tracks smoothly low behind her shoulders. A titanic 5-meter turquoise ocean swell rears up directly before her, arching into an ominous, hollow curling barrel with heavy aerated water mass. Intense offshore wind shears spindrift off the crest into the overcast sky. "
    "[4-8 seconds]: The heavy curving lip of the 5-meter wave pitches forward and crashes with thunderous hydraulic force onto the dark rocks directly in front of her feet, detonating into dense white churning seafoam, churning froth, and high-flying seawater spray mist. She remains completely fearless, calm and resolute, dress and hair violently billowing in the wind as water rushes around the rocky base. "
    "CINEMATOGRAPHY & LIGHTING: Master Prime 35mm lens, authentic natural overcast daylight, real atmospheric depth, true oceanic fluid physics and water weight, ARRI Alexa cinematic texture, absolutely zero plastic 3D cgi, zero anime style, zero symmetry."
)

async def main():
    print(f"=== Starting Generation for Scene 06: Towering 5m Wave ===")
    print(f"Target Image: {TARGET_IMG} (Exists: {os.path.exists(TARGET_IMG)})")

    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next((t for t in tabs if "flow.google.com" in t.get("url", "")), None)
    if not flow_tab:
        raise RuntimeError("No Google Flow tab found on port 9222!")

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
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

        # 1. Close popovers
        print("[Step 1] Dismissing popovers...")
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.3)
        await call_cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape"})
        await asyncio.sleep(0.5)

        # 2. Upload keyframe image via trusted mouse clicks & CDP file chooser interception
        print("[Step 2] Uploading keyframe image via CDP...")
        await call_cdp("Page.enable")
        await call_cdp("DOM.enable")
        await call_cdp("Page.setInterceptFileChooserDialog", {"enabled": True})

        get_menu_coords = """
        (() => {
            const btn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
            if (btn) {
                const r = btn.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
            return null;
        })()
        """
        res_btn = await call_cdp("Runtime.evaluate", {"expression": get_menu_coords, "returnByValue": True})
        c = res_btn.get("result", {}).get("value")
        if not c:
            raise RuntimeError("Could not find 'Medien hinzufügen' button!")

        await call_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": c["x"], "y": c["y"], "button": "left", "clickCount": 1})
        await call_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": c["x"], "y": c["y"], "button": "left", "clickCount": 1})
        await asyncio.sleep(0.6)

        get_h_coords = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const b = btns.find(el => (el.innerText || '').trim() === 'Hochladen' || (el.innerText || '').includes('Hochladen'));
            if (b) {
                const r = b.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
            return null;
        })()
        """
        res_h = await call_cdp("Runtime.evaluate", {"expression": get_h_coords, "returnByValue": True})
        h_coords = res_h.get("result", {}).get("value")
        if not h_coords:
            raise RuntimeError("Could not find 'Hochladen' item!")

        await call_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": h_coords["x"], "y": h_coords["y"], "button": "left", "clickCount": 1})
        await call_cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": h_coords["x"], "y": h_coords["y"], "button": "left", "clickCount": 1})
        print("Clicked Hochladen! Intercepting fileChooserOpened...")

        file_set = False
        for _ in range(15):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                msg = json.loads(raw)
                if msg.get("method") == "Page.fileChooserOpened":
                    print("Intercepted Page.fileChooserOpened!")
                    backend_id = msg["params"].get("backendNodeId")
                    set_params = {"files": [TARGET_IMG]}
                    if backend_id:
                        set_params["backendNodeId"] = backend_id
                    await call_cdp("DOM.setFileInputFiles", set_params)
                    file_set = True
                    break
            except asyncio.TimeoutError:
                pass

        if not file_set:
            raise RuntimeError("Failed to intercept fileChooserOpened!")

        print("File provided to file chooser! Waiting 7s for Flow upload to process...")
        await asyncio.sleep(7.0)

        # 3. Fresh chat session
        print("[Step 3] Starting fresh chat session...")
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
        print("New chat:", res_nc.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 4. Open '+' menu in prompt box
        print("[Step 4] Opening '+' menu in prompt box...")
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
        print("Prompt plus:", res_pp.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 5. Search and attach towering_wave_cand1
        print("[Step 5] Selecting towering wave image in popover...")
        select_img_js = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container, .flow-add-menu-dialog-panel, .mat-mdc-menu-panel') || document.body;
            const searchInput = popover.querySelector('input[type="search"], input[placeholder*="Suchen"], input[placeholder*="Search"], input');
            if (searchInput) {
                searchInput.focus();
                searchInput.value = 'towering_wave';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            // STRICT MATCH: No fallback to items[0]!
            const target = items.find(el => (el.innerText || '').toLowerCase().includes('towering_wave'));
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
            return { error: 'Target image towering_wave not found in popover' };
        })()
        """
        res_sel = await call_cdp("Runtime.evaluate", {"expression": select_img_js, "returnByValue": True})
        sel_val = res_sel.get("result", {}).get("value")
        print("Attachment result:", sel_val)
        if not sel_val or not sel_val.get("success"):
            raise RuntimeError(f"Attachment failed: {sel_val}")
        await asyncio.sleep(1.5)

        # 6. Insert prompt text
        print("[Step 6] Inserting temporal cinematic prompt...")
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
        print("Prompt insert:", res_p.get("result", {}).get("value"))
        await asyncio.sleep(1.5)

        # 7. Submit prompt
        print("[Step 7] Submitting prompt...")
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

        # 8. Immediate cost approval check (Iron Rule 6)
        print("[Step 8] Monitoring for Genehmigen / cost approval card...")
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
        for s in range(20):
            await asyncio.sleep(1.0)
            res_ap = await call_cdp("Runtime.evaluate", {"expression": approve_js, "returnByValue": True})
            val = res_ap.get("result", {}).get("value")
            if val and val != 'No card':
                print(f"Approval confirmed at s={s+1}: {val}")
                break

        # 9. Wait for video generation to reach 100%
        print("[Step 9] Monitoring video generation progress...")
        monitor_js = """
        (() => {
            const bodyText = document.body.innerText || '';
            const m = bodyText.match(/(\\d+)\\s*%/);
            const progress = m ? parseInt(m[1]) : null;

            // Check if there are active video player elements
            const videos = Array.from(document.querySelectorAll('video'));
            const hasReadyVideo = videos.some(v => v.src && v.duration > 0);

            // Check for download buttons
            const dlBtns = Array.from(document.querySelectorAll('button')).filter(b => {
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                const txt = (b.innerText || '').toLowerCase();
                return aria.includes('herunterladen') || aria.includes('download') || txt.includes('download');
            });

            return {
                progress: progress,
                videoCount: videos.length,
                hasReadyVideo: hasReadyVideo,
                hasDownloadBtn: dlBtns.length > 0
            };
        })()
        """
        start_time = time.time()
        completed = False
        while time.time() - start_time < 360:  # 6 minute timeout
            await asyncio.sleep(5.0)
            res_m = await call_cdp("Runtime.evaluate", {"expression": monitor_js, "returnByValue": True})
            state = res_m.get("result", {}).get("value") or {}
            elapsed = int(time.time() - start_time)
            prog = state.get("progress")
            print(f"[{elapsed}s] Progress: {prog}% | HasReadyVideo: {state.get('hasReadyVideo')} | HasDownloadBtn: {state.get('hasDownloadBtn')}")

            if state.get("progress") == 100 or (state.get("hasDownloadBtn") and elapsed > 30):
                print(f"Generation reached 100%! Ready to download.")
                completed = True
                await asyncio.sleep(3.0)
                break

        if not completed:
            print("Warning: Timed out waiting for 100% state. Will attempt download check...")

        # 10. Download video
        print("[Step 10] Triggering video download...")
        await call_cdp("Browser.setDownloadBehavior", {
            "behavior": "allowAndName",
            "downloadPath": CLIPS_DIR,
            "eventsEnabled": True
        })
        await call_cdp("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": CLIPS_DIR
        })

        files_before = set(os.listdir(CLIPS_DIR))

        click_dl = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button')).filter(b => {
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                const txt = (b.innerText || '').toLowerCase();
                return aria.includes('herunterladen') || aria.includes('download') || txt.includes('download');
            });
            if (btns.length > 0) {
                btns[0].click();
                return { success: true, aria: btns[0].getAttribute('aria-label'), text: btns[0].innerText };
            }
            return { error: 'No download button' };
        })()
        """
        res_dl = await call_cdp("Runtime.evaluate", {"expression": click_dl, "returnByValue": True})
        print("Download button click:", res_dl.get("result", {}).get("value"))
        await asyncio.sleep(1.0)

        # Check for 720p menuitem
        click_menu = """
        (() => {
            const menu = document.querySelector('.mat-mdc-menu-panel, [role="menu"]');
            if (!menu) return { menuFound: false };
            const items = Array.from(menu.querySelectorAll('[role="menuitem"], button'));
            const target = items.find(i => (i.innerText || '').toLowerCase().includes('720')) || items[0];
            if (target) {
                target.click();
                return { success: true, text: target.innerText };
            }
            return { error: 'No item in menu' };
        })()
        """
        res_menu = await call_cdp("Runtime.evaluate", {"expression": click_menu, "returnByValue": True})
        print("Menu selection:", res_menu.get("result", {}).get("value"))

        # Wait for file to arrive in CLIPS_DIR
        print("Waiting for file download to complete...")
        downloaded_file = None
        for _ in range(60):
            await asyncio.sleep(1.0)
            current_files = set(os.listdir(CLIPS_DIR))
            new_files = current_files - files_before
            mp4_new = [f for f in new_files if f.endswith(".mp4") and not f.endswith(".crdownload")]
            if mp4_new:
                downloaded_file = os.path.join(CLIPS_DIR, mp4_new[0])
                # Check size stability
                size1 = os.path.getsize(downloaded_file)
                await asyncio.sleep(1.0)
                size2 = os.path.getsize(downloaded_file)
                if size1 == size2 and size1 > 100000:
                    break

        if not downloaded_file or not os.path.exists(downloaded_file):
            # Fallback: check most recently modified mp4 in CLIPS_DIR
            all_mp4s = [os.path.join(CLIPS_DIR, f) for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")]
            all_mp4s.sort(key=os.path.getmtime, reverse=True)
            if all_mp4s and time.time() - os.path.getmtime(all_mp4s[0]) < 120:
                downloaded_file = all_mp4s[0]

        if not downloaded_file:
            raise RuntimeError("Download failed: No new MP4 found in clips dir!")

        print(f"Downloaded file: {downloaded_file} ({os.path.getsize(downloaded_file)} bytes)")

        # Rename / copy to FINAL_VIDEO_PATH
        if downloaded_file != FINAL_VIDEO_PATH:
            shutil.copy2(downloaded_file, FINAL_VIDEO_PATH)
            print(f"Saved to canonical path: {FINAL_VIDEO_PATH}")

        # Copy to artifact dir
        artifact_video = os.path.join(ARTIFACT_DIR, FINAL_VIDEO_NAME)
        shutil.copy2(FINAL_VIDEO_PATH, artifact_video)
        print(f"Copied to artifact dir: {artifact_video}")

        # 11. Extract QC frames (25%, 50%, 75%) and build contact sheet
        print("[Step 11] Building QC frames and contact sheet...")
        ffprobe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{FINAL_VIDEO_PATH}"'
        dur_res = subprocess.check_output(ffprobe_cmd, shell=True).decode().strip()
        duration = float(dur_res)
        print(f"Video duration: {duration:.2f}s")

        t25 = duration * 0.25
        t50 = duration * 0.50
        t75 = duration * 0.75

        frame25_path = os.path.join(ARTIFACT_DIR, "qc_wave_v1_25.png")
        frame50_path = os.path.join(ARTIFACT_DIR, "qc_wave_v1_50.png")
        frame75_path = os.path.join(ARTIFACT_DIR, "qc_wave_v1_75.png")
        contact_sheet_path = os.path.join(ARTIFACT_DIR, "qc_scene_towering_wave_v1.png")
        contact_sheet_local = os.path.join(CLIPS_DIR, "qc_scene_towering_wave_v1.png")

        subprocess.check_call(f'ffmpeg -y -ss {t25} -i "{FINAL_VIDEO_PATH}" -vframes 1 "{frame25_path}"', shell=True)
        subprocess.check_call(f'ffmpeg -y -ss {t50} -i "{FINAL_VIDEO_PATH}" -vframes 1 "{frame50_path}"', shell=True)
        subprocess.check_call(f'ffmpeg -y -ss {t75} -i "{FINAL_VIDEO_PATH}" -vframes 1 "{frame75_path}"', shell=True)

        im25 = Image.open(frame25_path).resize((426, 240))
        im50 = Image.open(frame50_path).resize((426, 240))
        im75 = Image.open(frame75_path).resize((426, 240))

        sheet = Image.new("RGB", (1280, 240), color=(10, 15, 20))
        sheet.paste(im25, (0, 0))
        sheet.paste(im50, (427, 0))
        sheet.paste(im75, (854, 0))
        sheet.save(contact_sheet_path, "PNG")
        sheet.save(contact_sheet_local, "PNG")
        print(f"QC Contact sheet created: {contact_sheet_path}")

        # 12. Open in user media player
        print("[Step 12] Launching video in media player on user desktop...")
        subprocess.Popen(f'explorer.exe "{FINAL_VIDEO_PATH}"', shell=True)

        print("\n=======================================================")
        print("SCENE 06 GENERATION COMPLETED SUCCESSFULLY!")
        print(f"Video: {FINAL_VIDEO_PATH}")
        print(f"Contact sheet: {contact_sheet_path}")
        print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
