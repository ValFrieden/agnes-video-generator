import asyncio
import json
import urllib.request
import websockets
import base64

async def click_last_genehmigen():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        click_script = """
        (() => {
            const elements = Array.from(document.querySelectorAll('.option-row, button, span, div'));
            const matches = elements.filter(el => {
                const txt = (el.innerText || '').trim();
                return (txt === 'Genehmigen' || txt === '✓ Genehmigen' || txt.includes('Genehmigen')) && 
                       !el.innerText.includes('immer') && 
                       !el.classList.contains('read-only');
            });
            if (matches.length > 0) {
                // Click the last one (most recent)
                const last = matches[matches.length - 1];
                const target = last.closest('.option-row') || last.closest('button') || last;
                target.scrollIntoView({ block: 'center' });
                target.click();
                const r = target.getBoundingClientRect();
                return {
                    success: true,
                    text: target.innerText.trim(),
                    coords: { x: r.x + r.width / 2, y: r.y + r.height / 2 }
                };
            }
            return { success: false, matches: matches.length };
        })()
        """
        req_id = 1
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                val = msg['result']['result']['value']
                print("Click Genehmigen result:", json.dumps(val, indent=2))
                break

        if val.get('success'):
            c = val['coords']
            # Also dispatch mouse click
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == 10: break
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == 11: break
            print("Mouse click confirmed!")

if __name__ == '__main__':
    asyncio.run(click_last_genehmigen())
