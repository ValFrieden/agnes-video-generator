import asyncio
import json
import urllib.request
import websockets

async def get_video_details():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const btn = document.querySelector('div[aria-label="Video im Editor öffnen"]');
            if (!btn) return { error: 'Button not found' };

            // Check attributes and data properties
            const keys = Object.keys(btn);
            let ngData = null;
            for (const k of keys) {
                if (k.startsWith('__ngContext__') || k.startsWith('__reactFiber')) {
                    ngData = k;
                }
            }

            // Click it to open in editor or player
            btn.click();

            return {
                clicked: true,
                ariaLabel: btn.getAttribute('aria-label'),
                className: btn.className,
                ngData
            };
        })()
        """
        cid = 108
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Click result:", json.dumps(res, indent=2))

        # Wait 2 seconds for editor/player modal or view to open
        await asyncio.sleep(2)

        # Check for new video elements or download buttons or urls
        check_after = """
        (() => {
            const videos = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src || v.currentSrc,
                duration: v.duration,
                paused: v.paused,
                width: v.videoWidth,
                height: v.videoHeight,
                parentClass: v.parentElement ? v.parentElement.className : ''
            }));

            // Find download button
            const downloadBtn = Array.from(document.querySelectorAll('button, a')).find(el => {
                const t = (el.innerText || el.getAttribute('aria-label') || '').toLowerCase();
                return t.includes('download') || t.includes('herunterladen') || t.includes('speichern');
            });

            return {
                videos,
                downloadBtn: downloadBtn ? (downloadBtn.innerText || downloadBtn.getAttribute('aria-label')) : null,
                downloadHref: downloadBtn ? downloadBtn.href : null
            };
        })()
        """
        cid2 = 109
        await ws.send(json.dumps({"id": cid2, "method": "Runtime.evaluate", "params": {"expression": check_after, "returnByValue": True}}))
        raw2 = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res2 = json.loads(raw2).get("result", {}).get("result", {}).get("value")
        print("After click state:", json.dumps(res2, indent=2))

if __name__ == "__main__":
    asyncio.run(get_video_details())
