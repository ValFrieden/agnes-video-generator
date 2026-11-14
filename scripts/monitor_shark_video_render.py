import asyncio
import json
import urllib.request
import websockets
import base64
import os
import sys

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Monitoring tab:", t["url"], flush=True)

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        for sec in range(0, 180, 5):
            await asyncio.sleep(5)
            
            script = """
            (() => {
                const textNodes = Array.from(document.querySelectorAll('div, span, p, .status-text, [class*="progress"]'))
                    .map(el => (el.innerText || '').trim())
                    .filter(t => t.includes('%') || t.includes('Generating') || t.includes('Processing') || t.includes('processing') || t.includes('ready'));
                
                // Get all video elements and video thumbnails
                const vids = Array.from(document.querySelectorAll('video, [data-media-type="video"], .video-container, .video-thumbnail'))
                    .map(v => ({
                        tag: v.tagName,
                        src: v.src || v.currentSrc,
                        aria: v.getAttribute('aria-label'),
                        className: v.className
                    }));

                const lastMessages = Array.from(document.querySelectorAll('.chat-message, [class*="message"], [class*="bubble"]'))
                    .map(m => (m.innerText || '').trim())
                    .filter(m => m.length > 0)
                    .slice(-3);

                return {
                    progressTexts: Array.from(new Set(textNodes)),
                    vidCount: vids.length,
                    lastVids: vids.slice(-3),
                    lastMessages
                };
            })()
            """
            await ws.send(json.dumps({'id': sec + 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            
            ptexts = val.get('progressTexts', [])
            print(f"[{sec}s] Progress texts: {ptexts}", flush=True)
            
            # Check if done
            # Look at last messages or if a new video has play button / download
            has_finished_msg = any('ready' in m.lower() or 'here is your video' in m.lower() or 'fertig' in m.lower() for m in val.get('lastMessages', []))
            
            # Take screenshot every 30s or when finished
            if sec % 30 == 0 or has_finished_msg:
                await ws.send(json.dumps({'id': 1000 + sec, 'method': 'Page.captureScreenshot'}))
                sc_res = json.loads(await ws.recv())
                with open('live_render_status.png', 'wb') as sf:
                    sf.write(base64.b64decode(sc_res['result']['data']))
                print(f"[{sec}s] Saved live_render_status.png", flush=True)

if __name__ == '__main__':
    asyncio.run(main())
