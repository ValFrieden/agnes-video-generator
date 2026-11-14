import asyncio
import json
import urllib.request
import websockets
import base64
import os

async def monitor():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Monitoring tab:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        for sec in range(0, 240, 5):
            await asyncio.sleep(5)
            
            script = """
            (() => {
                const textNodes = Array.from(document.querySelectorAll('div, span, p'))
                    .map(el => (el.innerText || '').trim())
                    .filter(t => t.includes('%') || t.includes('Generating') || t.includes('Processing') || t.includes('processing') || t.includes('ready') || t.includes('bereit'));
                
                const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                    src: v.src || v.currentSrc,
                    duration: v.duration,
                    rect: v.getBoundingClientRect()
                }));

                const lastBubble = Array.from(document.querySelectorAll('.agent-bubble, .message-bubble, .chat-message')).slice(-2).map(b => (b.innerText || '').slice(0, 200));

                return {
                    progressTexts: Array.from(new Set(textNodes)).slice(-5),
                    vidCount: vids.length,
                    vids,
                    lastBubble
                };
            })()
            """
            await ws.send(json.dumps({'id': sec + 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            
            ptexts = val.get('progressTexts', [])
            print(f"[{sec}s] Progress: {ptexts} | Videos: {val.get('vidCount')}", flush=True)

            # Check if video is finished
            # Look at lastBubble for completion
            bubble_txt = " ".join(val.get('lastBubble', [])).lower()
            if 'ready' in bubble_txt or 'fertig' in bubble_txt or 'here is' in bubble_txt or 'hier ist' in bubble_txt or (sec > 25 and not any('%' in t for t in ptexts)):
                print("Video appears ready! Taking screenshot...")
                await ws.send(json.dumps({'id': 1000 + sec, 'method': 'Page.captureScreenshot'}))
                sc_res = json.loads(await ws.recv())
                with open('live_video_v2_status.png', 'wb') as sf:
                    sf.write(base64.b64decode(sc_res['result']['data']))
                print("Saved live_video_v2_status.png")
                break

if __name__ == '__main__':
    asyncio.run(monitor())
