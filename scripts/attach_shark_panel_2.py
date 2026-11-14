import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Click shark_panel_2.jpg
        click_item = """
        (() => {
            const titles = Array.from(document.querySelectorAll('.asset-title, span, div'));
            const target = titles.find(el => (el.innerText || '').trim() === 'shark_panel_2.jpg');
            if (target) {
                target.click();
                // Also click parent card
                const card = target.closest('.asset-card, .gallery-item, .media-item, [class*="card"]');
                if (card) card.click();
                return { success: true, text: target.innerText };
            }
            return { success: false, error: 'shark_panel_2.jpg not found' };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_item, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Click shark_panel_2:", res['result']['result']['value'])
        await asyncio.sleep(0.5)

        # Step 2: Click "Zum Prompt hinzufügen"
        click_add_btn = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button, [role="button"], span'));
            const addBtn = btns.find(b => (b.innerText || '').trim() === 'Zum Prompt hinzufügen');
            if (addBtn) {
                // If it's a span inside a button, click the button
                const btn = addBtn.closest('button') || addBtn;
                btn.click();
                return { success: true, text: btn.innerText, disabled: btn.disabled };
            }
            return { success: false, error: 'Add button not found' };
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': click_add_btn, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Click Zum Prompt hinzufügen:", res2['result']['result']['value'])
        await asyncio.sleep(0.5)

        # Step 3: Check prompt box chips
        check_prompt = """
        (() => {
            const chips = Array.from(document.querySelectorAll('.chip, .image-chip, [class*="chip"], [class*="attachment"], [class*="pill"]'))
                .filter(c => c.getBoundingClientRect().width > 0)
                .map(c => ({ text: (c.innerText || '').trim(), aria: c.getAttribute('aria-label'), class: c.className }));
            return chips;
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': check_prompt, 'returnByValue': True}}))
        res3 = json.loads(await ws.recv())
        print("Prompt chips:", json.dumps(res3['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(main())
