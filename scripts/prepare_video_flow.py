import asyncio
import json
import urllib.request
import websockets

async def check_image_actions():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const imgs = Array.from(document.querySelectorAll('img[src*="flow.google.com/asb"]'));
            const lastImg = imgs[imgs.length - 1]; // option 2
            if (!lastImg) return {error: 'no img'};
            
            let el = lastImg;
            let container = null;
            for (let i = 0; i < 8; i++) {
                if (el.parentElement) {
                    el = el.parentElement;
                    if (el.querySelectorAll('button').length > 0) {
                        container = el;
                    }
                }
            }
            const btns = container ? Array.from(container.querySelectorAll('button')).map(b => ({
                text: b.innerText,
                title: b.title,
                aria: b.getAttribute('aria-label'),
                className: b.className
            })) : [];
            return {
                lastImgSrc: lastImg.src.slice(0, 80),
                containerClass: container ? container.className : null,
                btns
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(check_image_actions())
