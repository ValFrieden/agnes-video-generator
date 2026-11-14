import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const buttons = Array.from(document.querySelectorAll('button, .option-row, [role="button"]'));
            const genBtn = buttons.find(b => {
                const txt = (b.innerText || '').trim();
                return (txt.includes('Genehmigen') || txt.includes('Сгенерировать')) && !b.classList.contains('read-only') && !b.disabled;
            });
            if (!genBtn) return { error: 'Genehmigen not found' };
            
            genBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
            const rect = genBtn.getBoundingClientRect();
            return {
                text: genBtn.innerText.trim(),
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                w: rect.width,
                h: rect.height,
                inView: rect.top >= 0 && rect.bottom <= window.innerHeight
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        val = res['result']['result']['value']
        print("Genehmigen button info:", json.dumps(val, indent=2))
        
        if val.get('x'):
            cx, cy = val['x'], val['y']
            print(f"Clicking at ({cx}, {cy})...")
            # First element.click()
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button, .option-row, [role="button"]'));
                const genBtn = buttons.find(b => (b.innerText || '').trim().includes('Genehmigen') && !b.disabled);
                if (genBtn) { genBtn.click(); return 'Clicked via DOM'; }
                return 'Not found';
            })()
            """, 'returnByValue': True}}))
            print("DOM click:", (await ws.recv()))
            
            # Then mouse click
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Mouse click dispatched!")

if __name__ == '__main__':
    asyncio.run(check())
