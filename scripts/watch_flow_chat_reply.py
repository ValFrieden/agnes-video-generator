import asyncio
import json
import urllib.request
import websockets
import base64

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        for i in range(15):
            await asyncio.sleep(2)
            check_script = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button, .option-row, [role="button"]'));
                const genBtn = buttons.find(b => {
                    const txt = (b.innerText || '').trim();
                    return (txt.includes('Genehmigen') || txt.includes('Сгенерировать')) && !b.classList.contains('read-only') && !b.disabled;
                });
                
                const lastTexts = Array.from(document.querySelectorAll('div, p, span'))
                    .filter(el => el.innerText && el.innerText.trim().length > 0 && el.children.length === 0)
                    .map(el => el.innerText.trim())
                    .slice(-6);

                if (genBtn) {
                    genBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
                    const r = genBtn.getBoundingClientRect();
                    return { found_gen: true, text: genBtn.innerText, x: r.x + r.width/2, y: r.y + r.height/2, lastTexts };
                }
                return { found_gen: false, lastTexts };
            })()
            """
            await ws.send(json.dumps({'id': 100 + i, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            print(f"[{i*2}s]", val.get('lastTexts')[-2:])
            
            if val.get('found_gen'):
                print("Clicking Genehmigen at", val['x'], val['y'])
                await ws.send(json.dumps({'id': 200, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': val['x'], 'y': val['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                await ws.send(json.dumps({'id': 201, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': val['x'], 'y': val['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                print("Clicked!")

if __name__ == '__main__':
    asyncio.run(main())
