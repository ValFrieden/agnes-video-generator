import asyncio
import json
import urllib.request
import websockets
import base64

async def attach_traveler():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Click "Traveler facing giant sandstorm"
        click_item = """
        (() => {
            const container = document.querySelector('.add-menu-popover-container');
            const items = Array.from(container.querySelectorAll('mat-list-item, div, span'));
            const target = items.find(el => (el.innerText || '').trim().includes('Traveler facing giant sandstorm'));
            if (target) {
                const li = target.closest('mat-list-item') || target;
                li.click();
                return { success: true, text: target.innerText };
            }
            return { success: false, error: 'target not found' };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_item, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Click item result:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 2: Click "Zum Prompt hinzufügen"
        click_add = """
        (() => {
            const container = document.querySelector('.add-menu-popover-container');
            const btns = Array.from(container.querySelectorAll('button, span'));
            const addBtn = btns.find(b => (b.innerText || '').trim() === 'Zum Prompt hinzufügen');
            if (addBtn) {
                const b = addBtn.closest('button') || addBtn;
                b.click();
                return { success: true, text: 'Clicked Zum Prompt hinzufügen' };
            }
            return { success: false, error: 'Add button not found' };
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': click_add, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Click add result:", res2['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 3: Check prompt box state and chips
        check_prompt = """
        (() => {
            const promptBox = document.querySelector('.agent-panel-prompt-box');
            if (!promptBox) return { error: 'promptBox not found' };
            const chips = Array.from(promptBox.querySelectorAll('.chip, .image-chip, [class*="chip"], [aria-label*="Bildelement"], img'))
                .map(c => ({ text: (c.innerText || '').trim(), tag: c.tagName, src: c.src, aria: c.getAttribute('aria-label') }));
            return {
                chips,
                hasImage: chips.length > 0
            };
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': check_prompt, 'returnByValue': True}}))
        res3 = json.loads(await ws.recv())
        print("Prompt chips after attach:", json.dumps(res3['result']['result']['value'], indent=2))

        # Screenshot
        await ws.send(json.dumps({'id': 4, 'method': 'Page.captureScreenshot'}))
        s_res = json.loads(await ws.recv())
        with open('after_attach_sandstorm.png', 'wb') as sf:
            sf.write(base64.b64decode(s_res['result']['data']))
        print("Saved after_attach_sandstorm.png")

if __name__ == '__main__':
    asyncio.run(attach_traveler())
