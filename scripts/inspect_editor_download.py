import asyncio
import json
import urllib.request
import websockets
import base64
import os

async def inspect_editor_and_download():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
        async def call_cdp(method, params=None):
            cid = int(asyncio.get_event_loop().time() * 1000) % 1000000
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    msg = json.loads(raw)
                    if msg.get("id") == cid:
                        return msg.get("result", {})
                except asyncio.TimeoutError:
                    return None

        # Screenshot
        shot = await call_cdp("Page.captureScreenshot", {"format": "png"})
        if shot and "data" in shot:
            artifact_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
            shot_path = os.path.join(artifact_dir, "flow_editor_view.png")
            with open(shot_path, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print(f"Saved editor screenshot to {shot_path}")

        # Find the download button details and video element
        js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, a')).filter(el => {
                const t = (el.innerText || el.getAttribute('aria-label') || '').toLowerCase();
                return t.includes('download') || t.includes('herunterladen');
            }).map(b => ({
                tag: b.tagName,
                text: b.innerText,
                aria: b.getAttribute('aria-label'),
                href: b.href,
                className: b.className,
                rect: b.getBoundingClientRect()
            }));

            const allVideos = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src || v.currentSrc,
                duration: v.duration,
                width: v.videoWidth,
                height: v.videoHeight
            }));

            return {
                downloadButtons: btns,
                videos: allVideos
            };
        })()
        """
        res = await call_cdp("Runtime.evaluate", {"expression": js, "returnByValue": True})
        val = res.get("result", {}).get("value", {})
        print("Details:", json.dumps(val, indent=2))

if __name__ == "__main__":
    asyncio.run(inspect_editor_and_download())
