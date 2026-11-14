import asyncio
import json
import urllib.request
import websockets

async def check_prompt_area():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const chips = Array.from(document.querySelectorAll('.chip, .image-chip, [class*="chip"], [class*="pill"], [class*="attachment"], [class*="badge"]')).map(c => ({
                text: c.innerText,
                tag: c.tagName,
                class: c.className
            }));
            const imgChips = Array.from(document.querySelectorAll('img')).filter(i => {
                const r = i.getBoundingClientRect();
                return r.top > window.innerHeight - 250;
            }).map(i => ({src: i.src.slice(0, 80), rect: i.getBoundingClientRect()}));
            const box = document.querySelector('textarea, [contenteditable="true"]');
            return {
                chips,
                imgChips,
                promptText: box ? (box.value || box.innerText) : null
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(check_prompt_area())
