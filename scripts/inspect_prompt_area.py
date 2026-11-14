import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const buttons = Array.from(document.querySelectorAll('button, [role="button"], input[type="file"]')).map(b => {
                const rect = b.getBoundingClientRect();
                return {
                    tagName: b.tagName,
                    type: b.type,
                    id: b.id,
                    className: b.className,
                    text: (b.innerText || '').trim(),
                    aria: b.getAttribute('aria-label'),
                    visible: rect.width > 0 && rect.height > 0,
                    x: rect.x + rect.width / 2,
                    y: rect.y + rect.height / 2
                };
            }).filter(b => b.visible);
            return buttons;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        buttons = res['result']['result']['value']
        print(f"Total visible buttons: {len(buttons)}")
        for b in buttons:
            if any(k in (b['text'] + ' ' + (b['aria'] or '') + ' ' + b['className']).lower() for k in ['add', 'upload', 'bild', 'image', 'datei', 'file', 'media', 'plus', 'attach', 'hochladen', '+']):
                print(b)

if __name__ == '__main__':
    asyncio.run(main())
