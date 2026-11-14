import asyncio
import json
import urllib.request
import websockets
import os

async def main():
    abs_path = os.path.abspath('nikogda_ne_boyus_frames/shark_panel_2.jpg')
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
        await ws.recv()
        await ws.send(json.dumps({'id': 2, 'method': 'DOM.enable'}))
        await ws.recv()
        await ws.send(json.dumps({'id': 3, 'method': 'Page.setInterceptFileChooserDialog', 'params': {'enabled': True}}))
        await ws.recv()

        # Menu button coords
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 1611, 'y': 38, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 1611, 'y': 38, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await asyncio.sleep(0.5)

        # Hochladen coords
        await ws.send(json.dumps({'id': 20, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 1692, 'y': 86, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 21, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 1692, 'y': 86, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()

        for _ in range(15):
            raw = await ws.recv()
            msg = json.loads(raw)
            if msg.get('method') == 'Page.fileChooserOpened':
                print("fileChooserOpened details:", json.dumps(msg, indent=2))
                params = msg['params']
                backend_node_id = params.get('backendNodeId')
                print("BackendNodeId:", backend_node_id)
                
                # Call DOM.setFileInputFiles
                set_files_cmd = {
                    'id': 101,
                    'method': 'DOM.setFileInputFiles',
                    'params': {
                        'files': [abs_path],
                        'backendNodeId': backend_node_id
                    }
                }
                await ws.send(json.dumps(set_files_cmd))
                res = json.loads(await ws.recv())
                print("DOM.setFileInputFiles result:", res)
                break

        print("Waiting 5s to allow Flow to upload and register file...")
        await asyncio.sleep(5)
        print("Done!")

if __name__ == '__main__':
    asyncio.run(main())
