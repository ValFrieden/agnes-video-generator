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
        raw = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(raw)
        if data.get('id') == msg_id:
            return data.get('result', {})

async def main():
    ws_url = get_flow_ws()
    print('Connecting to:', ws_url)
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # First enable Runtime and Page
        await send_cmd(ws, 1, 'Runtime.enable')
        await send_cmd(ws, 2, 'Page.enable')

        # Inspect DOM
        script = """(() => {
            const msgs = Array.from(document.querySelectorAll('.message-bubble, flow-chat-message, [class*="message"]'))
                .map(m => m.innerText.trim()).filter(Boolean);
            const vids = Array.from(document.querySelectorAll('video'))
                .map(v => v.currentSrc || v.src).filter(Boolean);
            const tiles = Array.from(document.querySelectorAll('flow-video-tile, .video-container')).length;
            const beenden = document.body.innerText.includes('Beenden');
            return {
                lastMsgs: msgs.slice(-4),
                vids,
                tiles,
                isGenerating: beenden
            };
        })()"""
        eval_res = await send_cmd(ws, 3, 'Runtime.evaluate', {'expression': script, 'returnByValue': True})
        val = eval_res.get('result', {}).get('value', {})
        print('Status:', json.dumps(val, indent=2))

        # Take screenshot
        res = await send_cmd(ws, 4, 'Page.captureScreenshot', {'format': 'png'})
        if 'data' in res:
            with open('kuda_idu_frames/flow_now_cdp.png', 'wb') as f:
                f.write(base64.b64decode(res['data']))
            print('Saved kuda_idu_frames/flow_now_cdp.png')

asyncio.run(main())
