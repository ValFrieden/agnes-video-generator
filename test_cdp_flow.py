import json, asyncio, websockets, base64, urllib.request

def get_flow_ws_url():
    with urllib.request.urlopen('http://127.0.0.1:9222/json/list') as resp:
        tabs = json.loads(resp.read().decode('utf-8'))
    for tab in tabs:
        if 'flow.google.com' in tab.get('url', ''):
            return tab['webSocketDebuggerUrl']
    for tab in tabs:
        if tab.get('type') == 'page':
            return tab['webSocketDebuggerUrl']
    raise RuntimeError('Flow page not found')

async def main():
    ws_url = get_flow_ws_url()
    print('Connecting to:', ws_url)
    async with websockets.connect(ws_url) as ws:
        # 1. Take instant screenshot
        await ws.send(json.dumps({'id': 1, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
        resp = await ws.recv()
        data = json.loads(resp)
        b64 = data['result']['data']
        with open('kuda_idu_frames/flow_cdp_instant.png', 'wb') as f:
            f.write(base64.b64decode(b64))
        print('Saved kuda_idu_frames/flow_cdp_instant.png')

        # 2. Inspect prompt and chat elements
        script = """(() => {
            const pm = document.querySelector('.ProseMirror');
            const chips = Array.from(document.querySelectorAll('.chip, [class*="chip"], [class*="thumbnail"], [aria-label*="Entfernen"]')).map(c => c.innerText.trim());
            const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.innerText.trim(),
                aria: b.getAttribute('aria-label')
            })).filter(b => b.text || b.aria);
            return {
                pmText: pm ? pm.innerText.trim() : null,
                chips: chips,
                buttonsCount: buttons.length
            };
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        resp2 = await ws.recv()
        info = json.loads(resp2)['result']['result']['value']
        print('DOM info:', json.dumps(info, indent=2))

asyncio.run(main())
