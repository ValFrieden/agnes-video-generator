import asyncio
import json
import urllib.request
import websockets
import os

target_image = os.path.abspath("d:/Projects/VideoGenerator/nikogda_ne_boyus_frames/snake_valley_option2_1280x720.png")
print("Target image path:", target_image, "Exists:", os.path.exists(target_image))

async def upload_direct():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Get document and query selector for input[type="file"]
        await ws.send(json.dumps({'id': 1, 'method': 'DOM.getDocument'}))
        doc = None
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            if msg.get('id') == 1:
                doc = msg['result']['root']
                break
        
        # Query selector for input[type="file"]
        await ws.send(json.dumps({
            'id': 2,
            'method': 'DOM.querySelector',
            'params': {
                'nodeId': doc['nodeId'],
                'selector': 'input[type="file"]'
            }
        }))
        node_id = None
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            if msg.get('id') == 2:
                node_id = msg['result']['nodeId']
                print("Found file input nodeId:", node_id)
                break
        
        if not node_id:
            print("No file input node found!")
            return
            
        # Step 2: Call DOM.setFileInputFiles
        await ws.send(json.dumps({
            'id': 3,
            'method': 'DOM.setFileInputFiles',
            'params': {
                'nodeId': node_id,
                'files': [target_image]
            }
        }))
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            if msg.get('id') == 3:
                print("DOM.setFileInputFiles response:", msg)
                break
        
        # Trigger change / input event on the input
        js_trigger = """
        (() => {
            const inp = document.querySelector('input[type="file"]');
            if (inp && inp.files.length > 0) {
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                return { success: true, fileName: inp.files[0].name, size: inp.files[0].size };
            }
            return { error: 'No files or input' };
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': js_trigger, 'returnByValue': True}}))
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            if msg.get('id') == 4:
                print("Trigger event result:", msg.get('result', {}).get('result', {}).get('value'))
                break

        print("Waiting 5s for Flow upload to process...")
        await asyncio.sleep(5)

asyncio.run(upload_direct())
