import asyncio
import json
import urllib.request
import websockets
import base64

async def retry_and_approve():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Click "Noch einmal versuchen"
        click_retry = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, span, div'));
            const retry = btns.find(b => (b.innerText || '').trim().includes('Noch einmal versuchen') || (b.innerText || '').trim().includes('Try again'));
            if (retry) {
                const target = retry.closest('button') || retry;
                target.click();
                return { success: true, text: target.innerText.trim() };
            }
            return { success: false, error: 'retry button not found' };
        })()
        """
        req_id = 1
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': click_retry, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("Retry click result:", json.dumps(msg['result']['result']['value'], indent=2))
                break

        # Step 2: Immediately watch for Genehmigen (every 0.5s)
        print("Watching for Genehmigen card...")
        for sec in range(30):
            await asyncio.sleep(1)
            
            check_gen = """
            (() => {
                const elements = Array.from(document.querySelectorAll('.option-row, button, span'));
                const gen = elements.find(el => {
                    const txt = (el.innerText || '').trim();
                    return (txt === 'Genehmigen' || txt === '✓ Genehmigen' || txt.includes('Genehmigen')) && 
                           !el.innerText.includes('immer') && 
                           !el.classList.contains('read-only');
                });
                if (gen) {
                    const target = gen.closest('.option-row') || gen.closest('button') || gen;
                    target.click();
                    return { found: true, text: target.innerText.trim() };
                }
                return { found: false };
            })()
            """
            req_id = 100 + sec
            await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': check_gen, 'returnByValue': True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == req_id:
                    res = msg['result']['result']['value']
                    break
            
            if res.get('found'):
                print(f"[{sec}s] Genehmigen card found and clicked! Result:", res)
                break
            else:
                if sec % 2 == 0:
                    print(f"[{sec}s] Waiting for Genehmigen...")

        await asyncio.sleep(2)
        # Take screenshot
        req_id = 999
        await ws.send(json.dumps({'id': req_id, 'method': 'Page.captureScreenshot'}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                with open('after_retry_and_approved.png', 'wb') as f:
                    f.write(base64.b64decode(msg['result']['data']))
                print("Saved after_retry_and_approved.png")
                break

if __name__ == '__main__':
    asyncio.run(retry_and_approve())
