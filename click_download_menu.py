import json, asyncio, websockets, urllib.request

req = urllib.request.Request('http://127.0.0.1:9222/json/list')
with urllib.request.urlopen(req, timeout=3) as resp:
    tabs = json.loads(resp.read().decode('utf-8'))
ws_url = [t['webSocketDebuggerUrl'] for t in tabs if 'flow.google.com' in t.get('url', '')][0]

async def click_download():
    async with websockets.connect(ws_url) as ws:
        # Click the Herunterladen button
        script = """(() => {
            const dlBtn = document.querySelector('[aria-label*="Herunterladen"], [aria-label*="Download"]');
            if (dlBtn) {
                dlBtn.click();
                return { clicked: true, text: dlBtn.innerText || dlBtn.getAttribute('aria-label') };
            }
            return { clicked: false };
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        raw1 = await ws.recv()
        print('Click DL button:', json.loads(raw1)['result']['result']['value'])

        await asyncio.sleep(1)

        # Inspect open menu options
        inspect_menu = """(() => {
            const items = Array.from(document.querySelectorAll('[role="menuitem"], mat-option, .mat-mdc-menu-item, button, a'))
                .map(el => ({
                    text: el.innerText.trim(),
                    role: el.getAttribute('role'),
                    aria: el.getAttribute('aria-label')
                })).filter(i => i.text.includes('720') || i.text.includes('1080') || i.text.includes('MP4') || i.text.includes('Original') || i.text.includes('Download') || i.text.includes('Herunterladen'));
            return items;
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': inspect_menu, 'returnByValue': True}}))
        raw2 = await ws.recv()
        print('Menu items:', json.dumps(json.loads(raw2)['result']['result']['value'], indent=2))

asyncio.run(click_download())
