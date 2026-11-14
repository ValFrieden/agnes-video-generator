import asyncio
import json
import urllib.request
import websockets

async def inspect_prompt():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const box = document.querySelector('textarea, [contenteditable="true"]');
            const chips = Array.from(document.querySelectorAll('.chip, .image-chip, [class*="chip"], [class*="attachment"], [class*="pill"]'))
                .filter(c => c.getBoundingClientRect().width > 0)
                .map(c => ({ text: (c.innerText || '').trim(), aria: c.getAttribute('aria-label'), class: c.className }));
            
            const submitBtn = document.querySelector('button[aria-label="Generierung starten"], button.generate-icon-button, button.send-button') ||
                             Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('arrow_forward') || b.getAttribute('aria-label') === 'Generierung starten');
            
            return {
                boxFound: !!box,
                boxTag: box ? box.tagName : null,
                boxVal: box ? (box.value || box.innerText) : null,
                chips,
                submitFound: !!submitBtn,
                submitDisabled: submitBtn ? submitBtn.disabled : null
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Prompt state:", json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(inspect_prompt())
