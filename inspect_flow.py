import urllib.request, json, asyncio, websockets, base64, sys

sys.stdout.reconfigure(encoding='utf-8')

async def get_state():
    req = urllib.request.Request('http://127.0.0.1:9222/json/list')
    with urllib.request.urlopen(req) as r:
        tabs = json.loads(r.read())
    ws_url = None
    for t in tabs:
        if 'flow.google.com/project' in t.get('url', ''):
            ws_url = t['webSocketDebuggerUrl']
            break
    
    if not ws_url:
        print('Flow project tab not found!')
        return

    async with websockets.connect(ws_url) as ws:
        # capture screenshot
        await ws.send(json.dumps({'id': 101, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}))
        while True:
            resp = json.loads(await ws.recv())
            if resp.get('id') == 101:
                b64 = resp['result']['data']
                with open('kuda_idu_frames/live_shot.png', 'wb') as f:
                    f.write(base64.b64decode(b64))
                print('Screenshot saved to kuda_idu_frames/live_shot.png')
                break

        # inspect buttons
        script = """(() => {
            const btns = Array.from(document.querySelectorAll('button, [role="button"], a')).map(b => ({
                text: (b.innerText || '').trim(),
                aria: b.getAttribute('aria-label') || '',
                cls: b.className
            })).filter(b => b.text || b.aria);
            return btns;
        })()"""
        await ws.send(json.dumps({'id': 102, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        while True:
            resp = json.loads(await ws.recv())
            if resp.get('id') == 102:
                btns = resp['result']['result']['value']
                print(f'Total buttons: {len(btns)}')
                for b in btns:
                    combo = (b['text'] + ' ' + b['aria']).lower()
                    if any(w in combo for w in ['herunter', 'download', 'veo', 'video', 'fertig', 'play', 'abspielen']):
                        print('Action button:', b)
                break

asyncio.run(get_state())
