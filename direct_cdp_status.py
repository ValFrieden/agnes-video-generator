import asyncio
import websockets
import json
import base64
import urllib.request

async def send_cmd(ws, msg_id, method, params=None):
    req = {'id': msg_id, 'method': method, 'params': params or {}}
    await ws.send(json.dumps(req))
    while True:
        raw = await ws.recv()
        data = json.loads(raw)
        if data.get('id') == msg_id:
            return data

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode())
    flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
    ws_url = flow_tab['webSocketDebuggerUrl']
    print('Connecting directly to page WS:', ws_url)

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        # 1. Evaluate DOM
        eval_script = """
        (() => {
            const body = document.body.innerText;
            const isQueued = body.includes('currently queued') || body.includes('in der Warteschlange');
            const hasOverload = body.includes('Der KI-Agent ist derzeit stark ausgelastet');
            const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.currentSrc || v.src,
                duration: v.duration,
                paused: v.paused
            })).filter(v => v.src && v.src.startsWith('http'));
            
            const chatMessages = Array.from(document.querySelectorAll('flow-chat-message, .chat-message')).map(m => m.innerText.trim()).filter(Boolean);
            const lastMsg = chatMessages.length ? chatMessages[chatMessages.length - 1].slice(-200) : '';

            return { isQueued, hasOverload, vids, lastMsg };
        })()
        """
        res_eval = await send_cmd(ws, 1, 'Runtime.evaluate', {'expression': eval_script, 'returnByValue': True})
        val = res_eval.get('result', {}).get('result', {}).get('value', {})
        print('DOM EVAL:', json.dumps(val, indent=2, ensure_ascii=False))

        # 2. Screenshot (jpeg quality 80)
        res_snap = await send_cmd(ws, 2, 'Page.captureScreenshot', {'format': 'jpeg', 'quality': 80})
        img_data = base64.b64decode(res_snap['result']['data'])
        with open('d:/Projects/VideoGenerator/moy_mir_iz_snov_frames/debug_direct_cdp.jpg', 'wb') as f:
            f.write(img_data)
        print('Screenshot saved to debug_direct_cdp.jpg')

asyncio.run(main())
