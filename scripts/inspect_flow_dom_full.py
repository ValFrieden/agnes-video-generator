import asyncio
import json
import urllib.request
import websockets

async def inspect():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            // Find recent assets in the DOM
            const assets = Array.from(document.querySelectorAll('.asset-title, .media-title, [class*="title"], [class*="name"]'))
                .map(el => (el.innerText || '').trim())
                .filter(t => t.length > 2)
                .slice(0, 30);

            // Find chat header titles
            const chatHeader = document.querySelector('.agent-panel-header, [class*="header"]');
            const chatTitle = chatHeader ? chatHeader.innerText.trim() : null;

            // Find any video elements
            const videos = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src || v.currentSrc,
                duration: v.duration,
                paused: v.paused
            }));

            // Check if there are other threads/sessions
            const sessionItems = Array.from(document.querySelectorAll('[role="menuitem"], .session-item, [class*="session"], [class*="thread"]'))
                .map(el => (el.innerText || '').trim())
                .filter(t => t.length > 0);

            return {
                chatTitle,
                recentAssets: assets.slice(0, 20),
                videos,
                sessionItems: sessionItems.slice(0, 10)
            };
        })()
        """
        req_id = 1
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("DOM Inspection:", json.dumps(msg['result']['result']['value'], indent=2))
                break

if __name__ == '__main__':
    asyncio.run(inspect())
