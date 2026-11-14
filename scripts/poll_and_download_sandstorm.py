import asyncio
import json
import urllib.request
import websockets
import base64
import os
import sys

sys.path.insert(0, r"d:\Projects\VideoGenerator")
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    target_mp4 = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_sandstorm_haboob.mp4"
    print("Target MP4 path:", target_mp4)

    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        print("Polling rendering state (up to 180s)...")
        for i in range(18): # 18 * 10s = 180s
            await asyncio.sleep(10)
            
            check_state = """
            (() => {
                const stopBtn = Array.from(document.querySelectorAll('mat-icon')).find(m => (m.innerText || '').trim() === 'stop');
                const percentText = Array.from(document.querySelectorAll('*'))
                    .filter(el => el.children.length === 0 && /^\\d+\\s*%$/.test((el.innerText || '').trim()))
                    .map(el => el.innerText.trim())[0] || null;
                
                // Check if new video element or video tile exists
                const videoElements = document.querySelectorAll('video').length;
                const playIcons = Array.from(document.querySelectorAll('mat-icon')).filter(m => (m.innerText || '').trim() === 'play_arrow' || (m.innerText || '').trim() === 'play_circle').length;

                return {
                    isGenerating: !!stopBtn,
                    percent: percentText,
                    videoElements,
                    playIcons
                };
            })()
            """
            req_id = 100 + i
            await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': check_state, 'returnByValue': True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == req_id:
                    st = msg['result']['result']['value']
                    print(f"[{i*10}s] Render poll:", json.dumps(st))
                    break

            # If generation finished (stop button gone and at least 30s elapsed)
            if not st.get('isGenerating') and i >= 3:
                print("Generation complete! (isGenerating == False)")
                break

    # Download with GoogleFlowEngine
    print("Initializing GoogleFlowEngine to download latest video...")
    engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
    res = await engine.download_latest_video(target_mp4, resolution="720p", timeout_seconds=90)
    print("Download result:", res)
    await engine.close()

if __name__ == '__main__':
    asyncio.run(main())
