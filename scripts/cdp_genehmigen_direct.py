import asyncio
import json
import websockets
import urllib.request

async def monitor_and_approve():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        click_script = """
            (() => {
                const btns = Array.from(document.querySelectorAll('button, [role="button"], span, div'));
                const target = btns.find(b => {
                    const t = (b.innerText || '').trim();
                    return t === 'Genehmigen' || t === '✓ Genehmigen' || t.startsWith('Genehmigen');
                });
                if (target) {
                    target.click();
                    const p = target.closest('button');
                    if (p) p.click();
                    return true;
                }
                return false;
            })()
        """
        for i in range(30):
            msg = {'id': i + 10, 'method': 'Runtime.evaluate', 'params': {'expression': click_script}}
            await ws.send(json.dumps(msg))
            resp = json.loads(await ws.recv())
            val = resp.get('result', {}).get('result', {}).get('value')
            print(f'Poll {i+1}: clicked={val}')
            if val is True:
                print('SUCCESS: Genehmigen clicked via direct CDP!')
                break
            await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(monitor_and_approve())
