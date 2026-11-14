import asyncio
import json
import websockets
import urllib.request
import time

async def click_genehmigen_precise():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        # Get coordinates of the visible Genehmigen button in chat
        script = """
            (() => {
                const btns = Array.from(document.querySelectorAll('button, [role="button"], span, div'));
                const target = btns.find(b => {
                    const t = (b.innerText || '').trim();
                    return t === 'Genehmigen' || t === '✓ Genehmigen';
                });
                if (!target) return null;
                const btn = target.closest('button') || target.closest('[role="button"]') || target;
                const rect = btn.getBoundingClientRect();
                return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, text: target.innerText };
            })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        resp = json.loads(await ws.recv())
        val = resp.get('result', {}).get('result', {}).get('value')
        print('Target Genehmigen coords:', val)

        if val and val.get('x') and val.get('y'):
            x = val['x']
            y = val['y']
            print(f'Sending Input.dispatchMouseEvent at ({x}, {y})...')
            # mousePressed
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
            }))
            await ws.recv()
            await asyncio.sleep(0.1)
            # mouseReleased
            await ws.send(json.dumps({
                'id': 3,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
            }))
            await ws.recv()
            print('Mouse click event dispatched successfully!')

if __name__ == '__main__':
    asyncio.run(click_genehmigen_precise())
