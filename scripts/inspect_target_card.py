import asyncio
import json
import urllib.request
import websockets

async def inspect_target_card():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const allElements = Array.from(document.querySelectorAll('*'));
            const targetEl = allElements.find(el => (el.innerText || '').includes("I've started generating your video"));
            if (!targetEl) return { found: false };

            // Find its parent card / container
            let cur = targetEl;
            while (cur && cur !== document.body && !cur.classList.contains('message') && !cur.tagName.toLowerCase().includes('card') && !cur.classList.contains('container')) {
                cur = cur.parentElement;
            }

            const container = cur || targetEl.parentElement;
            const html = container ? container.outerHTML.slice(0, 1000) : 'no container';
            const videos = Array.from(container ? container.querySelectorAll('video') : []).map(v => v.src);
            const imgs = Array.from(container ? container.querySelectorAll('img') : []).map(i => i.src);

            // Also check all media in the project asset gallery / sidebar
            const galleryAssets = Array.from(document.querySelectorAll('.asset-thumbnail, .asset-item, .media-item, [class*="asset"]'))
                .slice(-10)
                .map(a => ({
                    text: (a.innerText || '').slice(0, 50),
                    img: a.querySelector('img') ? a.querySelector('img').src : null,
                    video: a.querySelector('video') ? a.querySelector('video').src : null
                }));

            return {
                found: true,
                targetText: targetEl.innerText.slice(0, 150),
                containerTag: container ? container.tagName : null,
                containerClass: container ? container.className : null,
                containerVideos: videos,
                containerImgs: imgs,
                htmlSnippet: html,
                galleryAssets
            };
        })()
        """
        cid = 106
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Target card info:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(inspect_target_card())
