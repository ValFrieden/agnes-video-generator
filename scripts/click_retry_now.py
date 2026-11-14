import asyncio
import json
import urllib.request
import websockets
import base64

async def find_and_click_retry():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const elements = Array.from(document.querySelectorAll('button, span, div, a'));
            const retry = elements.find(el => {
                const txt = (el.innerText || '').trim();
                return txt.includes('Noch einmal versuchen') || txt.includes('Try again');
            });
            if (retry) {
                const target = retry.closest('button') || retry;
                const r = target.getBoundingClientRect();
                return {
                    found: true,
                    text: target.innerText.trim(),
                    tag: target.tagName,
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2,
                    w: r.width,
                    h: r.height
                };
            }
            return { found: false };
        })()
        """
        req_id = 1
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                info = msg['result']['result']['value']
                print("Retry button info:", info)
                break

        if info.get('found'):
            cx, cy = info['x'], info['y']
            print(f"Dispatching click at ({cx}, {cy})...")
            # DOM click first
            req_id = 2
            await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': """
            (() => {
                const elements = Array.from(document.querySelectorAll('button, span, div, a'));
                const retry = elements.find(el => (el.innerText || '').trim().includes('Noch einmal versuchen'));
                if (retry) { (retry.closest('button') || retry).click(); return 'Clicked retry'; }
                return 'Not found';
            })()
            """, 'returnByValue': True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == req_id:
                    print("DOM click result:", msg['result']['result']['value'])
                    break

            # Mouse click as well
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == 10: break
            
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == 11: break
            print("Mouse click dispatched!")

if __name__ == '__main__':
    asyncio.run(find_and_click_retry())
