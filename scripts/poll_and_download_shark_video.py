import asyncio
import json
import urllib.request
import websockets
import base64
import os
import time

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    
    output_dir = "d:/Projects/VideoGenerator/nikogda_ne_boyus_frames/clips"
    os.makedirs(output_dir, exist_ok=True)
    target_mp4 = os.path.join(output_dir, "scene_sharks_realistic.mp4")
    
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        print("Connected to Flow. Polling render progress...")
        
        # We poll for up to 300 seconds (5 minutes)
        for second in range(0, 300, 5):
            await asyncio.sleep(5)
            
            # Check percentage or if finished
            status_script = """
            (() => {
                const textNodes = Array.from(document.querySelectorAll('*'))
                    .filter(el => el.children.length === 0 && (el.innerText || '').trim().length > 0)
                    .map(el => el.innerText.trim());
                
                const percentMatch = textNodes.find(t => /^\\d+\\s*%$/.test(t));
                
                // Check if top left tile has a video or is completed
                // In Flow, the gallery has asset tiles. Let's find all video elements or asset cards
                const assetTiles = Array.from(document.querySelectorAll('asset-tile, [data-asset-id], .asset-card, .media-tile, div.tile'));
                
                return {
                    percent: percentMatch || null,
                    textSample: textNodes.slice(0, 20)
                };
            })()
            """
            await ws.send(json.dumps({"id": 10 + second, "method": "Runtime.evaluate", "params": {"expression": status_script, "returnByValue": True}}))
            s_res = json.loads(await ws.recv())
            val = s_res["result"]["result"]["value"]
            pct = val.get("percent")
            
            if pct:
                print(f"[{second}s] Video rendering progress: {pct}")
            else:
                print(f"[{second}s] No percentage found - checking if rendering completed...")
                # Take a quick screenshot to check visual state
                await ws.send(json.dumps({"id": 1000 + second, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
                snap_res = json.loads(await ws.recv())
                snap_data = base64.b64decode(snap_res["result"]["data"])
                with open("d:/Projects/VideoGenerator/shark_poll_status.png", "wb") as f:
                    f.write(snap_data)
                
                # Check if there is a completed video in the top-left area (approx x: 280, y: 250)
                # Let's inspect the DOM for newly added video elements or asset cards
                inspect_video = """
                (() => {
                    const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                        src: v.src,
                        currentSrc: v.currentSrc,
                        duration: v.duration,
                        paused: v.paused
                    }));
                    return vids;
                })()
                """
                await ws.send(json.dumps({"id": 2000 + second, "method": "Runtime.evaluate", "params": {"expression": inspect_video, "returnByValue": True}}))
                v_res = json.loads(await ws.recv())
                vids = v_res["result"]["result"]["value"]
                print(f"Found {len(vids)} video elements:", vids)
                
                # If we see videos or percentage is gone after having started, it might be ready!
                if second >= 20 and not pct:
                    print("Render appears complete! Proceeding to inspect/open top-left video...")
                    break

if __name__ == "__main__":
    asyncio.run(main())
