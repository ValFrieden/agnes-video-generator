import json, asyncio, websockets, urllib.request

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
        # Dispatch mouse click at (1685, 687) -> center of Immer genehmigen
        print('Dispatching mouse click at (1685, 687)...')
        await send_cmd(ws, 1, 'Input.dispatchMouseEvent', {
            'type': 'mousePressed',
            'x': 1685,
            'y': 687,
            'button': 'left',
            'clickCount': 1
        })
        await asyncio.sleep(0.1)
        await send_cmd(ws, 2, 'Input.dispatchMouseEvent', {
            'type': 'mouseReleased',
            'x': 1685,
            'y': 687,
            'button': 'left',
            'clickCount': 1
        })

        await asyncio.sleep(2)

        # Inspect if generation started
        script = """(() => {
            const body = document.body.innerText || '';
            const match = body.match(/(\d+)\s*%/);
            const isGenerating = body.includes('Beenden') || body.includes('Generierung');
            const stillOptions = document.querySelectorAll('.option-label').length;
            return {
                pct: match ? match[1] : null,
                isGenerating,
                optionsCount: stillOptions,
                bodySnippet: body.slice(-250)
            };
        })()"""
        res = await send_cmd(ws, 3, 'Runtime.evaluate', {'expression': script, 'returnByValue': True})
        val = res.get('result', {}).get('value', {})
        print('Status after mouse click:', json.dumps(val, indent=2))

asyncio.run(main())
