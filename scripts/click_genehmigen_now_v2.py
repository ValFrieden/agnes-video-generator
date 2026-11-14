import asyncio
import json
import urllib.request
import websockets

async def click_gen():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
            const genBtn = buttons.find(b => (b.innerText || '').trim() === 'Genehmigen');
            if (genBtn) {
                const r = genBtn.getBoundingClientRect();
                return { found: true, x: r.x + r.width / 2, y: r.y + r.height / 2, text: genBtn.innerText };
            }
            return { found: false };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        val = res['result']['result']['value']
        print('Gen button:', val)
        if val.get('found'):
            await ws.send(json.dumps({'id': 2, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': val['x'], 'y': val['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 3, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': val['x'], 'y': val['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print('Clicked Genehmigen successfully!')

if __name__ == '__main__':
    asyncio.run(click_gen())
