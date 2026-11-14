import asyncio
import json
import urllib.request
import websockets
import base64

async def click_dom_genehmigen():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        click_code = """
        (() => {
            const elements = Array.from(document.querySelectorAll('.option-row, button, [role="button"], span'));
            const gen = elements.find(el => {
                const txt = (el.innerText || '').trim();
                return (txt === 'Genehmigen' || txt === '✓ Genehmigen' || txt.includes('Genehmigen')) && 
                       !el.innerText.includes('immer') && 
                       !el.classList.contains('read-only');
            });
            if (gen) {
                const target = gen.closest('.option-row') || gen.closest('button') || gen;
                target.click();
                return { success: true, text: target.innerText.trim() };
            }
            return { success: false };
        })()
        """
        req_id = 1
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': click_code, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("Click result:", json.dumps(msg['result']['result']['value'], indent=2))
                break

        await asyncio.sleep(2)

        # Screenshot
        req_id = 2
        await ws.send(json.dumps({'id': req_id, 'method': 'Page.captureScreenshot'}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                with open('after_dom_gen_click.png', 'wb') as f:
                    f.write(base64.b64decode(msg['result']['data']))
                print("Saved after_dom_gen_click.png")
                break

if __name__ == '__main__':
    asyncio.run(click_dom_genehmigen())
