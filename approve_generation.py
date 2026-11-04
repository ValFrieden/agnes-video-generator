import json, asyncio, websockets, base64, urllib.request

def get_flow_ws():
    req = urllib.request.Request('http://127.0.0.1:9222/json/list')
    with urllib.request.urlopen(req, timeout=3) as resp:
        tabs = json.loads(resp.read().decode('utf-8'))
    for t in tabs:
        if 'flow.google.com' in t.get('url', ''):
            return t['webSocketDebuggerUrl']
    for t in tabs:
        if t.get('type') == 'page':
            return t['webSocketDebuggerUrl']
    raise RuntimeError('Flow page not found')

async def send_cmd(ws, msg_id, method, params=None):
    payload = {'id': msg_id, 'method': method}
    if params:
        payload['params'] = params
    await ws.send(json.dumps(payload))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=15)
        data = json.loads(raw)
        if data.get('id') == msg_id:
            return data.get('result', {})

async def main():
    ws_url = get_flow_ws()
    print('Connecting to:', ws_url)
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        await send_cmd(ws, 1, 'Runtime.enable')
        await send_cmd(ws, 2, 'Page.enable')

        script = """(() => {
            const allElements = Array.from(document.querySelectorAll('button, div, span, [role="button"]'));
            const immer = allElements.find(el => el.innerText && el.innerText.trim().includes('Immer genehmigen'));
            if (immer) {
                immer.click();
                return { clicked: 'Immer genehmigen', tag: immer.tagName };
            }
            const genehmigen = allElements.find(el => el.innerText && el.innerText.trim() === 'Genehmigen');
            if (genehmigen) {
                genehmigen.click();
                return { clicked: 'Genehmigen', tag: genehmigen.tagName };
            }
            return { clicked: null };
        })()"""
        res = await send_cmd(ws, 3, 'Runtime.evaluate', {'expression': script, 'returnByValue': True})
        val = res.get('result', {}).get('value', {})
        print('Click result:', json.dumps(val, indent=2))

        await asyncio.sleep(2)

        # Check generation start
        check_script = """(() => {
            return {
                bodyText: document.body.innerText.slice(-300),
                hasBeenden: document.body.innerText.includes('Beenden')
            };
        })()"""
        res2 = await send_cmd(ws, 4, 'Runtime.evaluate', {'expression': check_script, 'returnByValue': True})
        val2 = res2.get('result', {}).get('value', {})
        print('Status after click:', json.dumps(val2, indent=2))

        # Capture screenshot
        shot_res = await send_cmd(ws, 5, 'Page.captureScreenshot', {'format': 'png'})
        if 'data' in shot_res:
            with open('kuda_idu_frames/flow_generating_now.png', 'wb') as f:
                f.write(base64.b64decode(shot_res['data']))
            print('Saved kuda_idu_frames/flow_generating_now.png')

asyncio.run(main())
