import asyncio
import json
import urllib.request
import websockets
import base64

async def click_add():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const promptBox = document.querySelector('.agent-panel-prompt-box');
            if (!promptBox) return { error: 'promptBox not found' };
            const addIcon = Array.from(promptBox.querySelectorAll('mat-icon')).find(i => (i.innerText || '').trim() === 'add');
            if (addIcon) {
                const btn = addIcon.closest('button');
                if (btn) {
                    btn.click();
                    return { success: true, text: 'clicked add button' };
                }
            }
            return { error: 'add button not found' };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Click add result:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Capture screenshot
        await ws.send(json.dumps({'id': 2, 'method': 'Page.captureScreenshot'}))
        s_res = json.loads(await ws.recv())
        with open('after_add_icon_click.png', 'wb') as sf:
            sf.write(base64.b64decode(s_res['result']['data']))
        print("Saved after_add_icon_click.png")

        # Check any menu that opened
        check_menu = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], .cdk-overlay-pane, div[class*="menu"]'))
                .filter(el => el.getBoundingClientRect().width > 0)
                .map(el => ({ text: (el.innerText || '').trim(), class: el.className }));
            return items;
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': check_menu, 'returnByValue': True}}))
        m_res = json.loads(await ws.recv())
        print("Menu items opened:", json.dumps(m_res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(click_add())
