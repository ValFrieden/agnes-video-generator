import asyncio
import json
import urllib.request
import websockets

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def click_btn():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        find = """(() => {
            const btns = Array.from(document.querySelectorAll('button, div[role="button"], span, div'));
            const b = btns.find(el => (el.innerText || '').trim() === 'Zum Prompt hinzufügen' && el.getBoundingClientRect().height > 15);
            if (b) {
                const r = b.getBoundingClientRect();
                return { tag: b.tagName, x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, h: r.height };
            }
            return null;
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': find, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        coords = res['result']['result']['value']
        print('Real button coords:', coords)

        if coords:
            cx, cy = coords['x'], coords['y']
            print(f'Clicking real button at ({cx}, {cy})...')
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await asyncio.sleep(0.1)
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print('Clicked!')

if __name__ == '__main__':
    asyncio.run(click_btn())
