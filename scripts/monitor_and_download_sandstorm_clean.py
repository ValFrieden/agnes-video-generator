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
    target_mp4 = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_sandstorm_haboob_v1.mp4"
    print("Target MP4 path:", target_mp4)

    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        print("Connected to Flow. Monitoring generation progress...")
        
        for i in range(25): # 25 * 8s = 200s
            await asyncio.sleep(8)
            
            script = """
            (() => {
                const stopBtn = Array.from(document.querySelectorAll('mat-icon')).find(m => (m.innerText || '').trim() === 'stop');
                
                // Check if top left tile in gallery is still placeholder or has image
                const firstTile = document.querySelector('.media-card, .asset-card, div.tile, [data-asset-id]');
                const firstTileImg = firstTile ? firstTile.querySelector('img') : null;
                
                // Check percentage text if any
                const pct = Array.from(document.querySelectorAll('*'))
                    .filter(el => el.children.length === 0 && /^\\d+\\s*%$/.test((el.innerText || '').trim()))
                    .map(el => el.innerText.trim())[0] || null;

                return {
                    isStreaming: !!stopBtn,
                    pct,
                    hasFirstTileImg: !!firstTileImg
                };
            })()
            """
            req_id = 100 + i
            await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == req_id:
                    st = msg['result']['result']['value']
                    print(f"[{i*8}s] Render poll:", json.dumps(st))
                    break

            # If stopped generating after at least 30 seconds
            if not st.get('isStreaming') and i >= 4:
                print("Generation complete! (isStreaming == False)")
                break

        # Save finished screenshot
        req_id = 999
        await ws.send(json.dumps({'id': req_id, 'method': 'Page.captureScreenshot'}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                with open('sandstorm_finished_snap.png', 'wb') as f:
                    f.write(base64.b64decode(msg['result']['data']))
                print("Saved sandstorm_finished_snap.png")
                break

    # Download with GoogleFlowEngine
    print("Calling GoogleFlowEngine.download_latest_video...")
    engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
    res = await engine.download_latest_video(target_mp4, resolution="720p", timeout_seconds=90)
    print("Download result:", res)
    await engine.close()

if __name__ == '__main__':
    asyncio.run(main())
