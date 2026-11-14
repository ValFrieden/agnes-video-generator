import asyncio
import json
import urllib.request
import websockets

async def test_insert():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const box = document.querySelector('[contenteditable="true"]');
            if (!box) return { error: 'contenteditable not found' };
            box.focus();
            // Select all and replace
            document.execCommand('selectAll', false, null);
            const ok = document.execCommand('insertText', false, 'Test sandstorm video');
            
            const submitBtn = document.querySelector('button[aria-label="Generierung starten"]');
            return {
                execOk: ok,
                text: box.innerText.trim(),
                submitDisabled: submitBtn ? submitBtn.disabled : null
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Insert test:", json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(test_insert())
