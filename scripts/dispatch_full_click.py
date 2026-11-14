import asyncio
import json
import websockets
import urllib.request

async def click_genehmigen_now():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        # Trigger full DOM click event sequence on the Genehmigen option
        script = """
            (() => {
                const els = Array.from(document.querySelectorAll('*'));
                const target = els.find(el => el.textContent && el.textContent.trim() === 'Genehmigen' && el.children.length === 0);
                if (!target) return 'NOT_FOUND';
                
                const card = target.closest('.cost-guard, .flow-permission-message, div');
                const btn = target.closest('button') || target.closest('[role="button"]') || target.parentElement;
                
                // Dispatch full pointer and mouse event chain
                const opts = { bubbles: true, cancelable: true, view: window };
                btn.dispatchEvent(new PointerEvent('pointerdown', opts));
                btn.dispatchEvent(new MouseEvent('mousedown', opts));
                btn.dispatchEvent(new PointerEvent('pointerup', opts));
                btn.dispatchEvent(new MouseEvent('mouseup', opts));
                btn.click();
                
                return { clicked: true, tagName: btn.tagName, className: btn.className };
            })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        resp = json.loads(await ws.recv())
        print('Click dispatch result:', resp.get('result', {}).get('result', {}).get('value'))

if __name__ == '__main__':
    asyncio.run(click_genehmigen_now())
