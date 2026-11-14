import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        click_add = """
        (() => {
            const btn = document.querySelector('button.add-menu-trigger, button[aria-label*="Prompt-Feld hinzufügen"]');
            if (btn) {
                btn.click();
                return 'Clicked add button in prompt box';
            }
            return 'Add button not found';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_add, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])
        await asyncio.sleep(0.5)

        script = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-panel *, [role="menu"] *, [role="listbox"] *, .cdk-overlay-container *'))
                .filter(el => el.innerText && el.innerText.trim().length > 0 && el.children.length === 0)
                .map(el => ({ tag: el.tagName, text: el.innerText.trim(), class: el.className }));
            return items;
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Overlay items:", json.dumps(res2['result']['result']['value'], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(check())
