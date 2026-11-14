import asyncio
import json
import websockets
import urllib.request

async def click_last_clickable_genehmigen():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        script = """
            (() => {
                // Find all option-rows that are NOT read-only and contain Genehmigen
                const rows = Array.from(document.querySelectorAll('.option-row:not(.read-only)'));
                const activeGenehmigen = rows.find(r => r.innerText.includes('Genehmigen'));
                if (!activeGenehmigen) return 'NO_ACTIVE_ROW';

                activeGenehmigen.scrollIntoView({ behavior: 'instant', block: 'center' });
                const rect = activeGenehmigen.getBoundingClientRect();
                return {
                    found: true,
                    x: rect.x + rect.width / 2,
                    y: rect.y + rect.height / 2,
                    class: activeGenehmigen.className,
                    text: activeGenehmigen.innerText
                };
            })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        resp = json.loads(await ws.recv())
        val = resp.get('result', {}).get('result', {}).get('value')
        print('Active Genehmigen button:', val)

        if isinstance(val, dict) and val.get('found'):
            x = val['x']
            y = val['y']
            print(f'Clicking active Genehmigen at ({x}, {y})...')
            await ws.send(json.dumps({
                'id': 2,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
            }))
            await ws.recv()
            await asyncio.sleep(0.1)
            await ws.send(json.dumps({
                'id': 3,
                'method': 'Input.dispatchMouseEvent',
                'params': {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
            }))
            await ws.recv()
            print('SUCCESS: Active Genehmigen clicked!')

if __name__ == '__main__':
    asyncio.run(click_last_clickable_genehmigen())
