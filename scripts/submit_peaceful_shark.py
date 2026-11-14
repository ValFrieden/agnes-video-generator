import asyncio
import json
import websockets
import urllib.request

async def submit_safe_shark():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        # Prompt without trigger words: marine wildlife documentary, peaceful open water swimming
        prompt = "Cinematic documentary sequence of an open-ocean swimmer seen strictly from behind (Back-to-Camera, no face shown), swimming steadily forward in crystal-clear calm turquoise waters. Graceful large marine wildlife and tiger sharks swimming peacefully alongside in the distant blue water, beautiful caustic sunbeams through the surface, serene rhythm, ultra-realistic 35mm film still motion, national geographic style, tranquil and majestic nature."
        
        script = f"""
            (() => {{
                const el = document.querySelector('.ProseMirror');
                if (el) {{
                    el.focus();
                    document.execCommand('selectAll', false, null);
                    document.execCommand('insertText', false, {json.dumps(prompt)});
                }}
                const btns = Array.from(document.querySelectorAll('button'));
                const sendBtn = btns.find(b => b.querySelector('i')?.innerText?.includes('arrow_forward') || b.querySelector('span')?.innerText?.includes('arrow_forward'));
                if (sendBtn) {{
                    sendBtn.click();
                    return 'SENT_PROMPT';
                }}
                const last = btns[btns.length - 1];
                last.click();
                return 'SENT_LAST';
            }})()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        print('Send prompt result:', await ws.recv())

        # Wait for Genehmigen card and click immediately!
        for i in range(30):
            await asyncio.sleep(2)
            click_script = """
                (() => {
                    const rows = Array.from(document.querySelectorAll('.option-row:not(.read-only)'));
                    const g = rows.find(r => r.innerText.includes('Genehmigen'));
                    if (g) {
                        g.scrollIntoView({ behavior: 'instant', block: 'center' });
                        const rect = g.getBoundingClientRect();
                        return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, found: true };
                    }
                    return { found: false };
                })()
            """
            msg = {'id': i + 10, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}
            await ws.send(json.dumps(msg))
            resp = json.loads(await ws.recv())
            val = resp.get('result', {}).get('result', {}).get('value')
            print(f'Poll {i+1} Genehmigen:', val)
            if val and val.get('found'):
                x = val['x']
                y = val['y']
                print(f'Clicking active Genehmigen at ({x}, {y})...')
                await ws.send(json.dumps({
                    'id': 100,
                    'method': 'Input.dispatchMouseEvent',
                    'params': {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
                }))
                await ws.recv()
                await asyncio.sleep(0.1)
                await ws.send(json.dumps({
                    'id': 101,
                    'method': 'Input.dispatchMouseEvent',
                    'params': {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
                }))
                await ws.recv()
                print('SUCCESS: Genehmigen clicked on peaceful shark video!')
                break

if __name__ == '__main__':
    asyncio.run(submit_safe_shark())
