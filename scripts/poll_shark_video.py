import asyncio
import json
import websockets
import urllib.request
import os
import subprocess
import time

async def poll_shark_video():
    clips_dir = 'd:/Projects/VideoGenerator/nikogda_ne_boyus_frames/clips'
    os.makedirs(clips_dir, exist_ok=True)
    out_video = os.path.join(clips_dir, 'scene_sharks.mp4')

    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        # Allow downloads
        await ws.send(json.dumps({
            'id': 1,
            'method': 'Page.setDownloadBehavior',
            'params': {'behavior': 'allow', 'downloadPath': os.path.abspath(clips_dir)}
        }))
        await ws.recv()

        for poll in range(60):
            await asyncio.sleep(5)
            # Check percentage in top-left tile
            script = """
                (() => {
                    const text = document.body.innerText;
                    const m = text.match(/(\\d{1,3})\\s*%/);
                    return m ? parseInt(m[1]) : null;
                })()
            """
            msg = {'id': poll + 10, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
            await ws.send(json.dumps(msg))
            resp = json.loads(await ws.recv())
            pct = resp.get('result', {}).get('result', {}).get('value')
            print(f'[Poll {poll+1}] Shark Video Render Progress: {pct}%')

            if pct == 100 or pct is None:
                # Video might be ready!
                # Check if top-left tile is done
                break

        print('Render complete or reached 100%! Looking for video URL / download...')
        
        # Extract video src from DOM if present
        get_vid_script = """
            (() => {
                const vids = Array.from(document.querySelectorAll('video')).map(v => v.src).filter(Boolean);
                return vids;
            })()
        """
        msg = {'id': 200, 'method': 'Runtime.evaluate', 'params': {'expression': get_vid_script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        vids = json.loads(await ws.recv()).get('result', {}).get('result', {}).get('value')
        print('Detected video URLs:', vids)

if __name__ == '__main__':
    asyncio.run(poll_shark_video())
