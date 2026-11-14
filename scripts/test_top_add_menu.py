import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        click_script = """
        (() => {
            const btn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
            if (btn) {
                btn.click();
                return { success: true, text: btn.innerText, aria: btn.getAttribute('aria-label') };
            }
            return { success: false, error: 'Button not found' };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Click result:", res['result']['result']['value'])
        
        await asyncio.sleep(1)
        
        inspect_menu = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-panel *, [role="menu"] *, [role="menuitem"]')).map(el => ({
                tag: el.tagName,
                role: el.getAttribute('role'),
                text: (el.innerText || '').trim(),
                className: el.className
            })).filter(x => x.text.length > 0 && x.text.length < 50);
            return items;
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': inspect_menu, 'returnByValue': True}}))
        m_res = json.loads(await ws.recv())
        print("Menu items:", json.dumps(m_res['result']['result']['value'], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
