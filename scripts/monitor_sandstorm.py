import asyncio
import json
import urllib.request
import websockets
import base64
import os

async def monitor():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        for i in range(24): # 24 * 5s = 120s
            await asyncio.sleep(5)
            
            script = """
            (() => {
                const textNodes = Array.from(document.querySelectorAll('*'))
                    .filter(el => el.children.length === 0 && (el.innerText || '').trim().length > 0)
                    .map(el => el.innerText.trim());
                
                const percentMatch = textNodes.find(t => /^\\d+\\s*%$/.test(t));
                
                // Check chat messages for completed video or processing status
                const chatTexts = Array.from(document.querySelectorAll('div, p, span'))
                    .filter(el => el.children.length === 0 && (el.innerText || '').trim().length > 0)
                    .map(el => el.innerText.trim())
                    .slice(-10);

                const hasNewVideo = Array.from(document.querySelectorAll('video, [aria-label*="Video"], [class*="video"]')).length;

                return {
                    percent: percentMatch || null,
                    chatTail: chatTexts,
                    hasNewVideo
                };
            })()
            """
            await ws.send(json.dumps({'id': 10 + i, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            
            print(f"[{i*5}s] Render status: percent={val.get('percent')}, chatTail={val.get('chatTail')[-3:]}")
            
            # If percentage reached 100% or disappeared after being high, or video player appears
            # Take screenshot
            if (i > 2 and not val.get('percent')) or i % 4 == 0:
                await ws.send(json.dumps({'id': 1000 + i, 'method': 'Page.captureScreenshot'}))
                s_res = json.loads(await ws.recv())
                with open('live_render_status.png', 'wb') as sf:
                    sf.write(base64.b64decode(s_res['result']['data']))

if __name__ == '__main__':
    asyncio.run(monitor())
