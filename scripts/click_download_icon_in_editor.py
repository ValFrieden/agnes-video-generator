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

        # 1. Set download behavior
        await call_cdp("Browser.setDownloadBehavior", {
            "behavior": "allowAndName",
            "downloadPath": CLIPS_DIR,
            "eventsEnabled": True
        })
        await call_cdp("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": CLIPS_DIR
        })

        # 2. Click the top-right download icon button in the header
        click_dl_btn = """
        (() => {
            // Find all buttons or mat-icons with download
            const icons = Array.from(document.querySelectorAll('mat-icon'));
            const dl = icons.find(i => ['download', 'file_download', 'arrow_downward'].includes((i.innerText || '').trim()));
            if (dl) {
                const btn = dl.closest('button') || dl;
                btn.click();
                return 'Clicked download icon in header';
            }
            const btns = Array.from(document.querySelectorAll('button')).filter(b => {
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                return aria.includes('download') || aria.includes('herunterladen');
            });
            if (btns.length > 0) {
                btns[0].click();
                return 'Clicked download button by aria';
            }
            return 'Not found';
        })()
        """
        res = await call_cdp("Runtime.evaluate", {"expression": click_dl_btn, "returnByValue": True})
        print("Click result:", res.get("result", {}).get("value"))

        # Check if a menu popped up (e.g. "Video (MP4)" or quality choices)
        await asyncio.sleep(1.0)
        click_mp4 = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
            const mp4Item = items.find(i => (i.innerText || '').includes('MP4') || (i.innerText || '').includes('Video') || (i.innerText || '').includes('Herunterladen'));
            if (mp4Item) {
                mp4Item.click();
                return 'Clicked MP4 item in menu: ' + mp4Item.innerText;
            }
            return 'No sub-item found';
        })()
        """
        res_sub = await call_cdp("Runtime.evaluate", {"expression": click_mp4, "returnByValue": True})
        print("Sub-menu click result:", res_sub.get("result", {}).get("value"))

        # Monitor CLIPS_DIR for newly downloaded mp4 file
        print("Monitoring CLIPS_DIR...", flush=True)
        before_files = set(os.listdir(CLIPS_DIR))
        new_file = None
        for sec in range(25):
            await asyncio.sleep(1.0)
            current_files = set(os.listdir(CLIPS_DIR))
            diff = current_files - before_files
            mp4s = [f for f in diff if f.endswith(".mp4") and not f.endswith(".crdownload")]
            if mp4s:
                new_file = os.path.join(CLIPS_DIR, mp4s[0])
                print(f"Downloaded new video: {new_file} after {sec+1}s!", flush=True)
                break

        if not new_file:
            # Check Downloads directory as fallback
            dl_dir = os.path.expanduser(r"~\Downloads")
            dl_files = [os.path.join(dl_dir, f) for f in os.listdir(dl_dir) if f.endswith('.mp4')]
            if dl_files:
                dl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                latest = dl_files[0]
                if time.time() - os.path.getmtime(latest) < 60:
                    new_file = latest
                    print("Found new file in Downloads:", new_file)

        if new_file:
            final_dest = os.path.join(CLIPS_DIR, "scene_firefighter_blaze_v1.mp4")
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
