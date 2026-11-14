import asyncio
import json
import websockets
import urllib.request

async def inspect_card_buttons():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        script = """
            (() => {
                const els = Array.from(document.querySelectorAll('.option-row, button, [role="button"], .action-button')).map(el => ({
                    text: el.innerText.trim(),
                    tag: el.tagName,
                    class: el.className
                }));
                return els.filter(r => r.text.includes('Genehmigen') || r.text.includes('Starten') || r.text.includes('Ablehnen'));
            })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        resp = json.loads(await ws.recv())
        print('Card elements:', resp.get('result', {}).get('result', {}).get('value'))

if __name__ == '__main__':
    asyncio.run(inspect_card_buttons())
