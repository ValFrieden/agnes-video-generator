import asyncio
import json
import urllib.request
import websockets
import base64

async def return_to_project():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Navigate back to main project URL
        project_url = 'https://flow.google.com/project/d7aa8d17-a219-4cf4-b840-832427562b58'
        print("Navigating back to:", project_url)
        await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': project_url}}))
        
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                break
        
        await asyncio.sleep(4)
        
        # Take screenshot
        await ws.send(json.dumps({'id': 2, 'method': 'Page.captureScreenshot'}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 2:
                with open('live_project_view.png', 'wb') as f:
                    f.write(base64.b64decode(msg['result']['data']))
                print("Saved live_project_view.png")
                break

if __name__ == '__main__':
    asyncio.run(return_to_project())
