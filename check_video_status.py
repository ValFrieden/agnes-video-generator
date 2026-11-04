import json, asyncio, websockets, urllib.request

req = urllib.request.Request('http://127.0.0.1:9222/json/list')
with urllib.request.urlopen(req, timeout=3) as resp:
    tabs = json.loads(resp.read().decode('utf-8'))
ws_url = [t['webSocketDebuggerUrl'] for t in tabs if 'flow.google.com' in t.get('url', '')][0]

async def check():
    async with websockets.connect(ws_url) as ws:
        script = """(() => {
            const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src || v.currentSrc,
                duration: v.duration,
                paused: v.paused
            }));
            const downloadBtns = Array.from(document.querySelectorAll('[aria-label*="Herunterladen"], [aria-label*="Download"], [aria-label*="download"]'))
                .map(b => b.getAttribute('aria-label') || b.innerText);
            const chatSnippets = Array.from(document.querySelectorAll('.message-bubble, flow-chat-message, [class*="message"]'))
                .map(m => m.innerText.trim()).filter(Boolean).slice(-3);
            return {
                videoTags: vids,
                downloadBtns,
                chatSnippets
            };
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        raw = await ws.recv()
        print(json.dumps(json.loads(raw)['result']['result']['value'], indent=2))

asyncio.run(check())
