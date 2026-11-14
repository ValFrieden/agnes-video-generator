import asyncio
import json
import websockets
import urllib.request

async def click_in_view():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        script = """
            (() => {
                const btns = Array.from(document.querySelectorAll('button, [role="button"], span, div'));
                const target = btns.find(b => {
                    const t = (b.innerText || '').trim();
                    return t === 'Genehmigen' || t === '✓ Genehmigen';
                });
                if (!target) return 'NOT_FOUND';
                const btn = target.closest('button') || target.closest('[role="button"]') || target;
                btn.scrollIntoView({ behavior: 'instant', block: 'center' });
                const r = btn.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height };
            })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        resp = json.loads(await ws.recv())
        val = resp.get('result', {}).get('result', {}).get('value')
        print('Scrolled Coords:', val)

        if isinstance(val, dict) and val.get('x') and val.get('y') > 0:
            x = val['x']
            y = val['y']
            print(f'Clicking at ({x}, {y})...')
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
            }))
            await ws.recv()
            await ws.send(json.dumps({
                'id': 3,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
            }))
            await ws.recv()
            print('SUCCESS: Mouse event sent to visible button!')

if __name__ == '__main__':
    asyncio.run(click_in_view())
