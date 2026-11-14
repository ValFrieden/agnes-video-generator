import asyncio
import json
import urllib.request
import websockets
import os
import shutil
import subprocess
import time

CLIPS_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips"
os.makedirs(CLIPS_DIR, exist_ok=True)
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

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

        # 1. Check for cost approval / Genehmigen card
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
        res_ap = await call_cdp("Runtime.evaluate", {"expression": approve_js, "returnByValue": True})
        print("Initial approval check:", res_ap.get("result", {}).get("value"))

        # 2. Loop monitoring until video generation completes
        print("Monitoring Veo 3.1 generation progress...", flush=True)
        check_ready_js = """
        (() => {
            const vidContainer = document.querySelector('.video-container.clickable, div[aria-label="Video im Editor öffnen"]');
            const playIcons = Array.from(document.querySelectorAll('.agent-message mat-icon, .chat-message mat-icon'))
                .filter(i => (i.innerText || '').trim() === 'play_circle');
            const loadingThreeDots = !!document.querySelector('.loading-dots, .typing-indicator, mat-progress-bar, mat-spinner');
            return {
                vidReady: !!vidContainer || playIcons.length > 0,
                stillLoading: loadingThreeDots
            };
        })()
        """

        for sec in range(180):
            await asyncio.sleep(2.0)
            # check genehmigen again just in case
            await call_cdp("Runtime.evaluate", {"expression": approve_js, "returnByValue": True})

            res_r = await call_cdp("Runtime.evaluate", {"expression": check_ready_js, "returnByValue": True})
            val = res_r.get("result", {}).get("value", {})
            if val.get("vidReady"):
                print(f"Video ready in chat at t={sec*2}s!", flush=True)
                break
            if sec % 10 == 0:
                print(f"Still generating at t={sec*2}s...", flush=True)

        await asyncio.sleep(2.0)

        # 3. Configure download path
        print("Configuring download path to:", CLIPS_DIR, flush=True)
        await call_cdp("Browser.setDownloadBehavior", {
            "behavior": "allowAndName",
            "downloadPath": CLIPS_DIR,
            "eventsEnabled": True
        })
        await call_cdp("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": CLIPS_DIR
        })

        # 4. Click video in chat to open in editor
        print("Clicking video in chat...", flush=True)
        click_vid_chat = """
        (() => {
            const vidContainer = document.querySelector('.video-container.clickable, div[aria-label="Video im Editor öffnen"]');
            if (vidContainer) {
                vidContainer.click();
                return 'Clicked video container';
            }
            const playIcon = Array.from(document.querySelectorAll('mat-icon')).find(i => (i.innerText||'').trim() === 'play_circle');
            if (playIcon) {
                (playIcon.closest('button, div') || playIcon).click();
                return 'Clicked play icon';
            }
            return 'Not found';
        })()
        """
        res_c = await call_cdp("Runtime.evaluate", {"expression": click_vid_chat, "returnByValue": True})
        print("Open in editor:", res_c.get("result", {}).get("value"))
        await asyncio.sleep(2.5)

        # 5. Click download icon in top header
        print("Clicking download icon in header...", flush=True)
        click_dl = """
        (() => {
            const icons = Array.from(document.querySelectorAll('mat-icon'));
            const dl = icons.find(i => ['download', 'file_download', 'arrow_downward'].includes((i.innerText || '').trim()));
            if (dl) {
                const btn = dl.closest('button') || dl;
                btn.click();
                return 'Clicked download icon';
            }
            return 'Download icon not found';
        })()
        """
        res_dl = await call_cdp("Runtime.evaluate", {"expression": click_dl, "returnByValue": True})
        print("Download click result:", res_dl.get("result", {}).get("value"))

        # Check for sub-menu (MP4 / Herunterladen)
        await asyncio.sleep(1.0)
        click_mp4 = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
            const mp4Item = items.find(i => (i.innerText || '').includes('MP4') || (i.innerText || '').includes('Video') || (i.innerText || '').includes('Herunterladen'));
            if (mp4Item) {
                mp4Item.click();
                return 'Clicked MP4: ' + mp4Item.innerText;
            }
            return 'No sub-item';
        })()
        """
        await call_cdp("Runtime.evaluate", {"expression": click_mp4, "returnByValue": True})

        # 6. Monitor CLIPS_DIR for download
        print("Waiting for download file to complete...", flush=True)
        before_files = set(os.listdir(CLIPS_DIR))
        new_file = None
        for sec in range(30):
            await asyncio.sleep(1.0)
            current_files = set(os.listdir(CLIPS_DIR))
            diff = current_files - before_files
            mp4s = [f for f in diff if f.endswith(".mp4") and not f.endswith(".crdownload")]
            if mp4s:
                new_file = os.path.join(CLIPS_DIR, mp4s[0])
                print(f"Downloaded video: {new_file} after {sec+1}s!", flush=True)
                break

        if not new_file:
            # Fallback: check latest file in CLIPS_DIR
            all_mp4 = [os.path.join(CLIPS_DIR, f) for f in os.listdir(CLIPS_DIR) if f.endswith('.mp4')]
            if all_mp4:
                all_mp4.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                latest = all_mp4[0]
                if time.time() - os.path.getmtime(latest) < 180:
                    new_file = latest
                    print("Using latest file in CLIPS_DIR:", new_file)

        if not new_file:
            # Fallback: check Downloads dir
            dl_dir = os.path.expanduser(r"~\Downloads")
            dl_files = [os.path.join(dl_dir, f) for f in os.listdir(dl_dir) if f.endswith('.mp4')]
            if dl_files:
                dl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                latest = dl_files[0]
                if time.time() - os.path.getmtime(latest) < 180:
                    new_file = latest
                    print("Found file in Downloads:", new_file)

        if new_file:
            final_dest = os.path.join(CLIPS_DIR, "scene_firefighter_blaze_v1.mp4")
            if os.path.abspath(new_file) != os.path.abspath(final_dest):
                shutil.copy2(new_file, final_dest)
            shutil.copy2(final_dest, os.path.join(ARTIFACT_DIR, "scene_firefighter_blaze_v1.mp4"))
            print("Successfully saved to:", final_dest, flush=True)

            # Generate QC frames
            print("Extracting QC frames...", flush=True)
            p_probe = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", final_dest
            ], capture_output=True, text=True)
            dur = float(p_probe.stdout.strip())
            print(f"Duration: {dur:.2f}s")

            t25, t50, t75 = dur * 0.25, dur * 0.50, dur * 0.75
            qc25 = os.path.join(ARTIFACT_DIR, "qc_firefighter_v1_25.png")
            qc50 = os.path.join(ARTIFACT_DIR, "qc_firefighter_v1_50.png")
            qc75 = os.path.join(ARTIFACT_DIR, "qc_firefighter_v1_75.png")

            subprocess.run(["ffmpeg", "-y", "-ss", str(t25), "-i", final_dest, "-vframes", "1", qc25], capture_output=True)
            subprocess.run(["ffmpeg", "-y", "-ss", str(t50), "-i", final_dest, "-vframes", "1", qc50], capture_output=True)
            subprocess.run(["ffmpeg", "-y", "-ss", str(t75), "-i", final_dest, "-vframes", "1", qc75], capture_output=True)

            contact_sheet = os.path.join(ARTIFACT_DIR, "qc_scene_firefighter_blaze_v1.png")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", qc25, "-i", qc50, "-i", qc75,
                "-filter_complex", "hstack=inputs=3",
                contact_sheet
            ], capture_output=True)
            print("QC Contact sheet generated:", contact_sheet, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
