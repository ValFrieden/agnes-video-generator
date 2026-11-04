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
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        script = """(() => {
            const bubbles = Array.from(document.querySelectorAll('.message-bubble, flow-chat-message, [class*="message"]'));
            const cards = Array.from(document.querySelectorAll('[class*="card"], [class*="tile"], [class*="video"]'));
            const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.currentSrc || v.src,
                duration: v.duration,
                paused: v.paused
            }));
            const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.innerText.trim(),
                aria: b.getAttribute('aria-label')
            })).filter(b => b.text || b.aria);
            return {
                lastBubbles: bubbles.slice(-4).map(b => b.innerText.trim()),
                cardsCount: cards.length,
                vids,
                bottomButtons: buttons.slice(-5)
            };
        })()"""
        res = await send_cmd(ws, 1, 'Runtime.evaluate', {'expression': script, 'returnByValue': True})
        val = res.get('result', {}).get('value', {})
        print(json.dumps(val, indent=2))

asyncio.run(main())
