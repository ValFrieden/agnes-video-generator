import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, [role="button"], span, div')).filter(el => {
                const txt = (el.innerText || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                return (txt.length > 0 && txt.length < 40) || aria.length > 0;
            }).map(el => {
                const r = el.getBoundingClientRect();
                return {
                    tag: el.tagName,
                    text: (el.innerText || '').trim(),
                    aria: el.getAttribute('aria-label'),
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2,
                    w: r.width,
                    h: r.height
                };
            }).filter(el => el.w > 0 && el.h > 0 && el.y > 0 && el.y < 1200);
            return btns;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        elements = res['result']['result']['value']
        for el in elements:
            combined = (el['text'] + ' ' + (el['aria'] or '')).lower()
            if any(k in combined for k in ['prompt', 'video', 'referenz', 'anfügen', 'hinzufügen', 'crop', 'zuschneiden', 'fertig']):
                print(el)

if __name__ == '__main__':
    asyncio.run(check())
