import asyncio
import json
import urllib.request
import websockets
import os
import time

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def click_exact_720():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        # Check if download menu is open, if not click download button first
        reopen = """(() => {
            const hasMenu = !!document.querySelector('.mat-mdc-menu-panel, [role="menu"]');
            if (!hasMenu) {
                const btns = Array.from(document.querySelectorAll('button'));
                const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen') || (b.innerText || '').toLowerCase().includes('download'));
                if (dl) {
                    dl.click();
                    return 'Reopened menu';
                }
                return 'DL button not found';
            }
            return 'Menu already open';
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': reopen, 'returnByValue': True}}))
        print("Menu state:", json.loads(await ws.recv())['result']['result']['value'])
        await asyncio.sleep(0.8)

        # Find 720p item coords
        find_coords = """(() => {
            const els = Array.from(document.querySelectorAll('.mat-mdc-menu-panel *, [role="menu"] *, [role="menuitem"], button'));
            const targets = els.filter(e => (e.innerText || '').trim().includes('720p'));
            // pick smallest bounding box (innermost)
            let best = null;
            let minArea = 1e9;
            for (const t of targets) {
                const r = t.getBoundingClientRect();
                const area = r.width * r.height;
                if (area > 10 && area < minArea) {
                    minArea = area;
                    best = { x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, h: r.height, text: t.innerText };
                }
            }
            return best;
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': find_coords, 'returnByValue': True}}))
        best = json.loads(await ws.recv())['result']['result']['value']
        print("Best 720p element:", best)

        if best:
            cx, cy = best['x'], best['y']
            print(f"Clicking at ({cx}, {cy})...")
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await asyncio.sleep(0.08)
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Real click dispatched to 720p menu item!")

if __name__ == '__main__':
    asyncio.run(click_exact_720())
