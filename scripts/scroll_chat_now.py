import asyncio
import json
import urllib.request
import websockets
import base64

async def scroll_and_check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        scroll_code = """
        (() => {
            const all = Array.from(document.querySelectorAll('*'));
            const scrollables = all.filter(el => {
                const style = window.getComputedStyle(el);
                return (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
            });
            
            scrollables.forEach(el => {
                el.scrollTop = el.scrollHeight;
            });
            
            return {
                scrollablesCount: scrollables.length,
                classes: scrollables.map(s => s.className)
            };
        })()
        """
        req_id = 1
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': scroll_code, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("Scroll result:", json.dumps(msg['result']['result']['value'], indent=2))
                break

        await asyncio.sleep(1)

        req_id = 2
        await ws.send(json.dumps({'id': req_id, 'method': 'Page.captureScreenshot'}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                with open('live_chat_scrolled.png', 'wb') as f:
                    f.write(base64.b64decode(msg['result']['data']))
                print("Saved live_chat_scrolled.png")
                break

if __name__ == '__main__':
    asyncio.run(scroll_and_check())
