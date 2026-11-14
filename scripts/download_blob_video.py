import asyncio
import json
import urllib.request
import websockets
import base64
import os

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
        # Get the video src
        get_src = """
        (() => {
            const vids = Array.from(document.querySelectorAll('video'));
            return vids.map(v => v.currentSrc || v.src);
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": get_src, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        sources = res["result"]["result"]["value"]
        print("Video sources:", sources)
        
        target_url = sources[0]
        print("Downloading from target URL:", target_url)
        
        # Download in chunks of base64 inside browser session
        # Let's see the size of the video via fetch
        fetch_script = f"""
        (async () => {{
            const resp = await fetch("{target_url}");
            const blob = await resp.blob();
            const reader = new FileReader();
            return new Promise((resolve) => {{
                reader.onloadend = () => {{
                    resolve({{ size: blob.size, dataUrl: reader.result }});
                }};
                reader.readAsDataURL(blob);
            }});
        }})()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": fetch_script, "awaitPromise": True, "returnByValue": True}}))
        blob_res = json.loads(await ws.recv())
        val = blob_res["result"]["result"]["value"]
        print("Blob size:", val.get("size"))
        
        data_url = val.get("dataUrl", "")
        # format: data:video/mp4;base64,...
        header, b64data = data_url.split(",", 1)
        video_bytes = base64.b64decode(b64data)
        
        dest_path = "d:/Projects/VideoGenerator/nikogda_ne_boyus_frames/clips/scene_sharks_realistic.mp4"
        with open(dest_path, "wb") as f:
            f.write(video_bytes)
        print(f"Successfully saved {len(video_bytes)} bytes to {dest_path}")

if __name__ == "__main__":
    asyncio.run(main())
