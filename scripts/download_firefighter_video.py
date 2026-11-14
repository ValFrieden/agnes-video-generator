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

        # 1. Configure download behavior
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

        # 2. Click download icon button at top right
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

        # 3. Check for dropdown menu and click 720p / Original
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
        res_m = await call_cdp("Runtime.evaluate", {"expression": click_menu, "returnByValue": True})
        print("Menu item click:", res_m.get("result", {}).get("value"))

        # 4. Wait for downloaded file in CLIPS_DIR
        print("Waiting for file download in CLIPS_DIR...", flush=True)
        initial_files = set(os.listdir(CLIPS_DIR))
        downloaded_file = None
        for _ in range(30):
            await asyncio.sleep(1.0)
            curr = set(os.listdir(CLIPS_DIR))
            new_f = [f for f in (curr - initial_files) if not f.endswith('.crdownload') and not f.endswith('.tmp') and f.endswith('.mp4')]
            if new_f:
                downloaded_file = os.path.join(CLIPS_DIR, new_f[0])
                print(f"Downloaded file found: {downloaded_file}", flush=True)
                break

        if not downloaded_file:
            # Fallback: check Downloads dir
            dl_dir = os.path.expanduser(r"~\Downloads")
            dl_files = [os.path.join(dl_dir, f) for f in os.listdir(dl_dir) if f.endswith('.mp4')]
            if dl_files:
                dl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                latest = dl_files[0]
                if time.time() - os.path.getmtime(latest) < 60:
                    downloaded_file = latest
                    print("Found recent file in Downloads:", downloaded_file)

        if not downloaded_file:
            print("Download timed out or not detected!", flush=True)
            return

        # 5. Copy to canonical path
        dest_canonical = os.path.join(CLIPS_DIR, "scene_firefighter_blaze_v1.mp4")
        shutil.copy2(downloaded_file, dest_canonical)
        artifact_video = os.path.join(ARTIFACT_DIR, "scene_firefighter_blaze_v1.mp4")
        shutil.copy2(dest_canonical, artifact_video)
        print(f"Copied to {dest_canonical} and {artifact_video}", flush=True)

        # 6. QC: Extract 25%, 50%, 75% frames with ffmpeg
        cmd_probe = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{dest_canonical}"'
        duration_str = subprocess.check_output(cmd_probe, shell=True).decode().strip()
        duration = float(duration_str)
        print(f"Video duration: {duration:.2f} seconds")

        t25 = duration * 0.25
        t50 = duration * 0.50
        t75 = duration * 0.75

        f25 = os.path.join(ARTIFACT_DIR, "qc_firefighter_v1_25.png")
        f50 = os.path.join(ARTIFACT_DIR, "qc_firefighter_v1_50.png")
        f75 = os.path.join(ARTIFACT_DIR, "qc_firefighter_v1_75.png")
        cs_path = os.path.join(ARTIFACT_DIR, "qc_scene_firefighter_blaze_v1.png")

        subprocess.run(f'ffmpeg -y -ss {t25:.2f} -i "{dest_canonical}" -vframes 1 "{f25}"', shell=True, check=True)
        subprocess.run(f'ffmpeg -y -ss {t50:.2f} -i "{dest_canonical}" -vframes 1 "{f50}"', shell=True, check=True)
        subprocess.run(f'ffmpeg -y -ss {t75:.2f} -i "{dest_canonical}" -vframes 1 "{f75}"', shell=True, check=True)

        # Build horizontal 3-panel contact sheet (1920x360)
        cmd_cs = (
            f'ffmpeg -y -i "{f25}" -i "{f50}" -i "{f75}" '
            f'-filter_complex "[0:v]scale=640:360[v0];[1:v]scale=640:360[v1];[2:v]scale=640:360[v2];[v0][v1][v2]hstack=inputs=3[out]" '
            f'-map "[out]" "{cs_path}"'
        )
        subprocess.run(cmd_cs, shell=True, check=True)

        # Copy to project qc folder
        qc_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\qc"
        os.makedirs(qc_dir, exist_ok=True)
        shutil.copy2(f25, os.path.join(qc_dir, "qc_firefighter_v1_25.png"))
        shutil.copy2(f50, os.path.join(qc_dir, "qc_firefighter_v1_50.png"))
        shutil.copy2(f75, os.path.join(qc_dir, "qc_firefighter_v1_75.png"))
        shutil.copy2(cs_path, os.path.join(qc_dir, "qc_scene_firefighter_blaze_v1.png"))

        print("\n>>> All Firefighter QC artifacts generated successfully! <<<", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
