import asyncio
import json
import urllib.request
import websockets
import base64
import os
import sys

sys.path.insert(0, r"d:\Projects\VideoGenerator")
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    
    target_mp4 = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\clips\scene_sandstorm_haboob.mp4"
    print("Will save final video to:", target_mp4)

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        print("Connected to Flow. Polling render status...")
        
        for i in range(40): # 40 * 5s = 200s
            await asyncio.sleep(5)
            
            script = """
            (() => {
                const textNodes = Array.from(document.querySelectorAll('*'))
                    .filter(el => el.children.length === 0 && (el.innerText || '').trim().length > 0)
                    .map(el => el.innerText.trim());
                
                const percentMatch = textNodes.find(t => /^\\d+\\s*%$/.test(t));
                
                // Check if any cost card or approval card appears
                const costCard = textNodes.find(t => t.includes('Guthabenpunkte') || t.includes('Genehmigen'));
                
                // Check chat messages for completed video or processing status
                const chatTexts = textNodes.slice(-12);

                const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                    src: v.src || v.currentSrc,
                    duration: v.duration,
                    paused: v.paused
                }));

                return {
                    percent: percentMatch || null,
                    costCard: !!costCard,
                    vidsCount: vids.length,
                    chatTexts: chatTexts.slice(-4)
                };
            })()
            """
            await ws.send(json.dumps({'id': 100 + i, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            
            pct = val.get('percent')
            print(f"[{i*5}s] Render poll: pct={pct}, costCard={val.get('costCard')}, chat={val.get('chatTexts')}")

            # If a Genehmigen button appears again, click it immediately!
            if val.get('costCard'):
                click_gen = """
                (() => {
                    const btn = Array.from(document.querySelectorAll('button, .option-row')).find(b => {
                        const t = (b.innerText || '').trim();
                        return (t === 'Genehmigen' || t.includes('Genehmigen')) && !b.innerText.includes('immer');
                    });
                    if (btn) {
                        btn.click();
                        return true;
                    }
                    return false;
                })()
                """
                await ws.send(json.dumps({'id': 200 + i, 'method': 'Runtime.evaluate', 'params': {'expression': click_gen, 'returnByValue': True}}))
                await ws.recv()

            # Take screenshot every 20s
            if i % 4 == 0:
                await ws.send(json.dumps({'id': 1000 + i, 'method': 'Page.captureScreenshot'}))
                s_res = json.loads(await ws.recv())
                with open('sandstorm_render_progress.png', 'wb') as sf:
                    sf.write(base64.b64decode(s_res['result']['data']))

            # If render completed (e.g. video player in chat with duration > 0 or new video)
            # Check if chat contains video player thumbnail for the new video
            check_done = """
            (() => {
                const stopBtn = document.querySelector('button mat-icon.google-symbols');
                const isStreaming = Array.from(document.querySelectorAll('*')).some(el => el.classList && el.classList.contains('streaming'));
                const lastMsg = document.querySelector('.chat-history')?.lastElementChild || document.body;
                const hasPlayer = !!document.querySelector('.video-player, video, [aria-label*="Video abspielen"]');
                return { isStreaming, hasPlayer };
            })()
            """

    # Now use GoogleFlowEngine to download the latest video!
    print("Calling GoogleFlowEngine.download_latest_video...")
    engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
    res = await engine.download_latest_video(target_mp4, resolution="720p", timeout_seconds=90)
    print("Download result:", res)
    await engine.close()

if __name__ == '__main__':
    asyncio.run(main())
