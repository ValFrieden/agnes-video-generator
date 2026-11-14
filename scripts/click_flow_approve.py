import asyncio
import json
import urllib.request
import websockets

async def click_approve():
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read().decode())
    flow_tab = next(t for t in tabs if 'flow.google.com' in t.get('url', ''))
    async with websockets.connect(flow_tab['webSocketDebuggerUrl']) as ws:
        js = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, div[role="button"], .option-row, span'));
            // Look for Genehmigen or Im Projekt immer genehmigen
            for (const b of btns) {
                const txt = (b.innerText || '').trim();
                if (txt.includes('Im Projekt immer genehmigen')) {
                    (b.closest('button') || b.closest('.option-row') || b).click();
                    return 'Clicked Im Projekt immer genehmigen: ' + txt;
                }
            }
            for (const b of btns) {
                const txt = (b.innerText || '').trim();
                if (txt === 'Genehmigen' || txt.startsWith('Genehmigen')) {
                    (b.closest('button') || b.closest('.option-row') || b).click();
                    return 'Clicked Genehmigen: ' + txt;
                }
            }
            return 'Not found';
        })()
        """
        cid = 101
        await ws.send(json.dumps({'id': cid, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get('result', {}).get('result', {}).get('value')
        print('Result:', res)

if __name__ == '__main__':
    asyncio.run(click_approve())
