import asyncio
import json
import urllib.request
import websockets
import os

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Click on Videos in left navigation
        click_videos_nav = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, a'));
            const vBtn = btns.find(b => (b.innerText || '').includes('Videos'));
            if (vBtn) {
                vBtn.click();
                return 'Clicked Videos nav';
            }
            return 'Videos nav not found';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_videos_nav, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])
        await asyncio.sleep(1)

        # Inspect videos and find video elements/links
        find_vids = """
        (() => {
            const vids = Array.from(document.querySelectorAll('video, [data-media-type="video"], .video-container, .video-thumbnail, img[src*="videofx"]')).map(el => {
                const r = el.getBoundingClientRect();
                return {
                    tag: el.tagName,
                    src: el.src || el.currentSrc,
                    aria: el.getAttribute('aria-label'),
                    class: el.className,
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2
                };
            });
            return vids;
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': find_vids, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Videos in view:", json.dumps(res2['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(main())
