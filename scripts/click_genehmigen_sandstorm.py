import asyncio
import json
import urllib.request
import websockets
import base64

async def click_genehmigen_now():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        find_btn = """
        (() => {
            const elements = Array.from(document.querySelectorAll('button, .option-row, [role="button"], div, span'));
            const gen = elements.find(el => {
                const txt = (el.innerText || '').trim();
                return (txt === 'Genehmigen' || txt === '✓ Genehmigen') && !el.classList.contains('read-only');
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
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': find_btn, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        val = res['result']['result']['value']
        print("Genehmigen button info:", val)

        if val.get('found'):
            c = val['coords']
            print(f"Clicking Genehmigen at ({c['x']}, {c['y']})...")
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Clicked successfully!")

            await asyncio.sleep(2)
            await ws.send(json.dumps({'id': 20, 'method': 'Page.captureScreenshot'}))
            s_res = json.loads(await ws.recv())
            with open('after_real_genehmigen_sandstorm.png', 'wb') as sf:
                sf.write(base64.b64decode(s_res['result']['data']))
            print("Saved after_real_genehmigen_sandstorm.png")

if __name__ == '__main__':
    asyncio.run(click_genehmigen_now())
