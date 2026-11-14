import asyncio
import json
import urllib.request
import websockets
import base64

async def click_genehmigen_fast():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Find Genehmigen element
        expr = """
        (() => {
            const elements = Array.from(document.querySelectorAll('button, .option-row, [role="button"], div, span'));
            const gen = elements.find(el => {
                const txt = (el.innerText || '').trim();
                return (txt === 'Genehmigen' || txt === '✓ Genehmigen' || txt.includes('Genehmigen')) && 
                       !el.classList.contains('read-only') && 
                       !el.innerText.includes('immer');
            });
            if (gen) {
                const target = gen.closest('.option-row') || gen.closest('button') || gen;
                target.scrollIntoView({ block: 'center' });
                const r = target.getBoundingClientRect();
                return {
                    found: true,
                    text: target.innerText.trim(),
                    coords: { x: r.x + r.width / 2, y: r.y + r.height / 2 }
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
                val = msg['result']['result']['value']
                print("Genehmigen button info:", val)
                break

        if val.get('found'):
            c = val['coords']
            print(f"Clicking at ({c['x']}, {c['y']})...")
            # mousePressed
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
            while True:
                m = json.loads(await ws.recv())
                if m.get('id') == 10: break
            
            # mouseReleased
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
            while True:
                m = json.loads(await ws.recv())
                if m.get('id') == 11: break
            print("Dispatched click on Genehmigen!")

            await asyncio.sleep(1.5)
            # Take snap
            await ws.send(json.dumps({'id': 20, 'method': 'Page.captureScreenshot'}))
            while True:
                m = json.loads(await ws.recv())
                if m.get('id') == 20:
                    with open('after_sandstorm_confirmed.png', 'wb') as sf:
                        sf.write(base64.b64decode(m['result']['data']))
                    print("Saved after_sandstorm_confirmed.png")
                    break

if __name__ == '__main__':
    asyncio.run(click_genehmigen_fast())
