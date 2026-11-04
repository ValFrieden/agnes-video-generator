import asyncio
import websockets
import json
import base64
import urllib.request
import os
import subprocess
import time

OUT_CLEAN_VIDEO = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_07_clean.mp4'
QA_25 = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_s07_qa_25.jpg'
QA_50 = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_s07_qa_50.jpg'
QA_75 = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_s07_qa_75.jpg'

async def send_cmd(ws, msg_id, method, params=None):
    req = {'id': msg_id, 'method': method, 'params': params or {}}
    await ws.send(json.dumps(req))
    while True:
        raw = await ws.recv()
        data = json.loads(raw)
        if data.get('id') == msg_id:
            return data

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode())
    flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
    ws_url = flow_tab['webSocketDebuggerUrl']
    print(f'Starting monitor on {ws_url}...', flush=True)

    start_time = time.time()
    max_wait = 1800 # 30 min

    # Keep track of Downloads folder
    dl_folder = os.path.join(os.environ.get('USERPROFILE', 'C:/Users/Valeri'), 'Downloads')
    initial_files = os.listdir(dl_folder) if os.path.exists(dl_folder) else []

    msg_id = 1
    while time.time() - start_time < max_wait:
        await asyncio.sleep(15)
        elapsed = int(time.time() - start_time)

        try:
            async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
                check_script = """
                (() => {
                    const body = document.body.innerText;
                    const isQueued = body.includes('currently queued') || body.includes('in der Warteschlange');
                    const hasSpinner = !!document.querySelector('mat-spinner, mat-progress-spinner, [role="progressbar"], .loading-spinner');
                    const vids = Array.from(document.querySelectorAll('video')).map(v => v.src || v.currentSrc).filter(Boolean);
                    
                    // Check if new video tile appeared or chat video has src
                    const chatVid = document.querySelector('flow-chat-message video, .chat-message video');
                    const chatVidSrc = chatVid ? (chatVid.src || chatVid.currentSrc) : '';

                    return { isQueued, hasSpinner, vidsCount: vids.length, chatVidSrc };
                })()
                """
                msg_id += 1
                res = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': check_script, 'returnByValue': True})
                val = res.get('result', {}).get('result', {}).get('value', {})
                print(f'[{elapsed}s] Status: isQueued={val.get("isQueued")}, hasSpinner={val.get("hasSpinner")}, vidsCount={val.get("vidsCount")}', flush=True)

                if not val.get('isQueued') and not val.get('hasSpinner'):
                    print('Queue finished! Clicking video card to download...', flush=True)
                    click_script = """
                    (() => {
                        const chatVid = document.querySelector('flow-chat-message video, .chat-message video, flow-chat-item video');
                        if (chatVid) {
                            chatVid.click();
                            return 'clicked_chat_vid';
                        }
                        const tile1 = document.querySelectorAll('flow-video-tile, .canvas-tile, .media-tile')[1];
                        if (tile1) {
                            tile1.click();
                            return 'clicked_tile1';
                        }
                        return 'no_tile';
                    })()
                    """
                    msg_id += 1
                    res_click = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': click_script, 'returnByValue': True})
                    print('Click result:', res_click.get('result', {}).get('result', {}).get('value'), flush=True)
                    await asyncio.sleep(2)

                    # Trigger download menu
                    dl_script = """
                    (() => {
                        const dlBtn = document.querySelector('button[aria-label*="Herunterladen"], button[aria-label*="Download"]');
                        if (dlBtn) {
                            dlBtn.click();
                            return 'clicked_dl_btn';
                        }
                        return 'no_dl_btn';
                    })()
                    """
                    msg_id += 1
                    res_dl = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': dl_script, 'returnByValue': True})
                    print('DL button result:', res_dl.get('result', {}).get('result', {}).get('value'), flush=True)
                    await asyncio.sleep(1)

                    # Click 720p option
                    menu_script = """
                    (() => {
                        const items = Array.from(document.querySelectorAll('[role="menuitem"], .mat-mdc-menu-item'));
                        const item720 = items.find(el => el.innerText.includes('720') || el.innerText.includes('MP4') || el.innerText.includes('Original'));
                        if (item720) {
                            item720.click();
                            return 'clicked_720';
                        }
                        return 'no_720_option';
                    })()
                    """
                    msg_id += 1
                    res_menu = await send_cmd(ws, msg_id, 'Runtime.evaluate', {'expression': menu_script, 'returnByValue': True})
                    print('720p option result:', res_menu.get('result', {}).get('result', {}).get('value'), flush=True)

                    # Wait for download to land
                    for _ in range(30):
                        await asyncio.sleep(1)
                        if os.path.exists(dl_folder):
                            current_files = [f for f in os.listdir(dl_folder) if f.endswith('.mp4') and f not in initial_files]
                            if current_files:
                                latest = max(current_files, key=lambda f: os.path.getmtime(os.path.join(dl_folder, f)))
                                src = os.path.join(dl_folder, latest)
                                if os.path.getsize(src) > 100000 and not latest.endswith('.crdownload'):
                                    import shutil
                                    shutil.copyfile(src, OUT_CLEAN_VIDEO)
                                    print(f'Successfully copied {latest} to {OUT_CLEAN_VIDEO}', flush=True)
                                    
                                    # Extract QA frames
                                    subprocess.run(['ffmpeg', '-y', '-ss', '00:00:02', '-i', OUT_CLEAN_VIDEO, '-vframes', '1', QA_25], capture_output=True)
                                    subprocess.run(['ffmpeg', '-y', '-ss', '00:00:04', '-i', OUT_CLEAN_VIDEO, '-vframes', '1', QA_50], capture_output=True)
                                    subprocess.run(['ffmpeg', '-y', '-ss', '00:00:06', '-i', OUT_CLEAN_VIDEO, '-vframes', '1', QA_75], capture_output=True)
                                    print('QA frames extracted!', flush=True)

                                    # Run assembly
                                    res_asm = subprocess.run(['python', 'd:/Projects/VideoGenerator/assemble_final_clip.py'], capture_output=True, text=True)
                                    print('Assembly output:', res_asm.stdout, flush=True)
                                    return
        except Exception as e:
            print(f'Iteration error: {e}', flush=True)

asyncio.run(main())
