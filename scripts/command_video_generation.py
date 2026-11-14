import asyncio
import json
import websockets
import urllib.request

async def command_video_generation():
    with urllib.request.urlopen('http://127.0.0.1:9222/json') as r:
        tabs = json.loads(r.read().decode())
        flow_tab = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]
        ws_url = flow_tab['webSocketDebuggerUrl']

    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        # Command directly: Create a VIDEO using Veo 3.1 - Fast
        prompt = "Create an 8-second video with Veo 3.1 - Fast using the first swimmer image above as image reference. Swimmer seen from behind swimming in calm turquoise ocean with sharks."
        
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
                    return 'SENT_ARROW';
                }}
                const last = btns[btns.length - 1];
                last.click();
                return 'SENT_LAST';
            }})()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        print('Send video command result:', await ws.recv())

        # Continuously monitor and click Genehmigen!
        for i in range(40):
            await asyncio.sleep(2)
            check_script = """
                (() => {
                    const rows = Array.from(document.querySelectorAll('.option-row:not(.read-only)'));
                    const g = rows.find(r => r.innerText.includes('Genehmigen'));
                    if (g) {
                        g.scrollIntoView({ behavior: 'instant', block: 'center' });
                        const rect = g.getBoundingClientRect();
                        return { found: true, x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
                    }
                    return { found: false };
                })()
            """
            msg = {'id': i + 10, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}
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
                print('SUCCESS: Genehmigen clicked!')
                break

if __name__ == '__main__':
    asyncio.run(command_video_generation())
