import json, asyncio, websockets, sys

sys.stdout.reconfigure(encoding='utf-8')

async def clear_tray():
    uri = 'ws://127.0.0.1:9222/devtools/page/0E7BD9B8349EB35B98566144FF51F46A'
    async with websockets.connect(uri, max_size=50*1024*1024) as ws:
        msg_id = 1

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {'id': msg_id, 'method': method}
            if params:
                payload['params'] = params
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get('id') == msg_id:
                    return resp.get('result', {})

        # Clear all attached media chips
        clear_script = """(() => {
            // Find all remove/close buttons on chips or media container
            const closeBtns = Array.from(document.querySelectorAll('button, mat-icon, span, div')).filter(el => {
                const text = (el.innerText || '').trim();
                const aria = (el.getAttribute('aria-label') || '').trim();
                return text === 'close' || aria.includes('Entfernen') || aria.includes('entfernen') || aria.includes('löschen');
            });

            let clickedCount = 0;
            closeBtns.forEach(btn => {
                try {
                    btn.click();
                    clickedCount++;
                } catch(e) {}
            });

            // Also clear ProseMirror text
            const pm = document.querySelector('.ProseMirror');
            if (pm) {
                pm.innerText = '';
                pm.dispatchEvent(new Event('input', { bubbles: true }));
            }

            return { clickedCount };
        })()"""

        res = await send('Runtime.evaluate', {'expression': clear_script, 'returnByValue': True})
        print('Clear result:', res.get('result', {}).get('value'))

asyncio.run(clear_tray())
