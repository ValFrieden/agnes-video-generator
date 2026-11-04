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

    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        # Evaluate state
        eval_script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean);
            const body = document.body.innerText;
            const isOverloaded = body.includes('Der KI-Agent ist derzeit stark ausgelastet');
            const hasTryAgain = btns.some(t => t.includes('Noch einmal versuchen') || t.includes('Try again'));
            const isGenerating = btns.some(t => t.includes('Beenden') || t.includes('Cancel'));
            const vids = Array.from(document.querySelectorAll('video')).map(v => v.src || v.currentSrc).filter(Boolean);
            return { isOverloaded, hasTryAgain, isGenerating, vidsCount: vids.length, buttons: btns.slice(0, 15) };
        })()
        """
        res_eval = await send_cmd(ws, 1, 'Runtime.evaluate', {'expression': eval_script, 'returnByValue': True})
        val = res_eval.get('result', {}).get('result', {}).get('value', res_eval)
        print('Flow DOM status:', json.dumps(val, indent=2, ensure_ascii=False))

        # Screenshot
        res_snap = await send_cmd(ws, 2, 'Page.captureScreenshot', {'format': 'png'})
        img_data = base64.b64decode(res_snap['result']['data'])
        with open('d:/Projects/VideoGenerator/moy_mir_iz_snov_frames/debug_cdp_live.png', 'wb') as f:
            f.write(img_data)
        print('Captured debug_cdp_live.png')

asyncio.run(main())
