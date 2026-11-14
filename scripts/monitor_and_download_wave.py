import asyncio
import json
import urllib.request
import websockets
import os
import shutil
import subprocess
import time
from PIL import Image

CLIPS_DIR = os.path.abspath(r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips")
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
FINAL_VIDEO_NAME = "scene_towering_wave_v1.mp4"
FINAL_VIDEO_PATH = os.path.join(CLIPS_DIR, FINAL_VIDEO_NAME)

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))

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

        # Check chat state
        check_chat_state = """
        (() => {
            const chatMsgs = Array.from(document.querySelectorAll('.chat-turn, .agent-turn, [class*="message"], .chat-history'));
            const lastTurn = chatMsgs.length > 0 ? chatMsgs[chatMsgs.length - 1].innerText : document.body.innerText;
            
            // Look for progress bar or spinner in the chat
            const spinners = document.querySelectorAll('mat-spinner, mat-progress-bar, [role="progressbar"], .loading');
            
            // Check video elements
            const videos = Array.from(document.querySelectorAll('video'));
            const videoSources = videos.map(v => ({ src: v.src, duration: v.duration, paused: v.paused }));
            
            // Look for download buttons
            const dlBtns = Array.from(document.querySelectorAll('button')).filter(b => {
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                const txt = (b.innerText || '').toLowerCase();
                return aria.includes('herunterladen') || aria.includes('download') || txt.includes('download');
            });
            
            // Check the status text in the last message
            const isProcessing = /actively processed|wird verarbeitet|in bearbeitung/i.test(document.body.innerText);

            return {
                isProcessing: isProcessing,
                spinnersCount: spinners.length,
                videoCount: videos.length,
                videoSources: videoSources,
                dlBtnCount: dlBtns.length
            };
        })()
        """

        print("Monitoring Veo 3.1 generation in Google Flow...")
        start_time = time.time()
        for i in range(120): # up to 6 minutes
            await asyncio.sleep(5.0)
            res = await call_cdp("Runtime.evaluate", {"expression": check_chat_state, "returnByValue": True})
            val = res.get("result", {}).get("value") or {}
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Processing: {val.get('isProcessing')} | Videos: {val.get('videoCount')} | DL Buttons: {val.get('dlBtnCount')}", flush=True)

            # If no longer processing or we have download buttons/ready video
            if not val.get("isProcessing") or val.get("dlBtnCount", 0) > 0:
                print(f"Generation seems completed at {elapsed}s! Checking for download...", flush=True)
                break

        # Configure download
        print("Configuring download behavior to:", CLIPS_DIR)
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

        # Click the video in the chat to open it or click its download button
        click_video_card = """
        (() => {
            // Find video card or container in the chat
            const chatVideo = document.querySelector('.agent-turn video, .chat-turn video, .agent-message video') ||
                              document.querySelector('video');
            if (chatVideo) {
                chatVideo.click();
                return 'Clicked chat video';
            }
            return 'No video element found';
        })()
        """
        res_cv = await call_cdp("Runtime.evaluate", {"expression": click_video_card, "returnByValue": True})
        print("Click video card:", res_cv.get("result", {}).get("value"))
        await asyncio.sleep(1.0)

        # Click download button
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

        # Check for 720p option in menu
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

        # Wait for file download
        print("Waiting for file download...")
        downloaded_file = None
        for _ in range(60):
            await asyncio.sleep(1.0)
            current_files = set(os.listdir(CLIPS_DIR))
            new_files = current_files - files_before
            mp4_new = [f for f in new_files if f.endswith(".mp4") and not f.endswith(".crdownload")]
            if mp4_new:
                downloaded_file = os.path.join(CLIPS_DIR, mp4_new[0])
                size1 = os.path.getsize(downloaded_file)
                await asyncio.sleep(1.0)
                size2 = os.path.getsize(downloaded_file)
                if size1 == size2 and size1 > 100000:
                    break

        if not downloaded_file:
            # Fallback: check newest mp4
            all_mp4s = [os.path.join(CLIPS_DIR, f) for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")]
            all_mp4s.sort(key=os.path.getmtime, reverse=True)
            if all_mp4s and time.time() - os.path.getmtime(all_mp4s[0]) < 180:
                downloaded_file = all_mp4s[0]

        if not downloaded_file:
            print("Download still pending or not triggered. Taking snapshot to inspect...")
            return

        print(f"Downloaded file: {downloaded_file} ({os.path.getsize(downloaded_file)} bytes)")
        if downloaded_file != FINAL_VIDEO_PATH:
            shutil.copy2(downloaded_file, FINAL_VIDEO_PATH)

        artifact_video = os.path.join(ARTIFACT_DIR, FINAL_VIDEO_NAME)
        shutil.copy2(FINAL_VIDEO_PATH, artifact_video)
        print(f"Copied to artifact dir: {artifact_video}")

        # QC Trio and contact sheet
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

        subprocess.Popen(f'explorer.exe "{FINAL_VIDEO_PATH}"', shell=True)
        print("ALL DONE SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
