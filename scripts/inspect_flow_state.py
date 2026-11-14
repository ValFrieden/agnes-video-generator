import asyncio
import json
import urllib.request
import websockets
import base64
import os
import sys

async def main():
    try:
        req = urllib.request.urlopen("http://localhost:9222/json")
        tabs = json.loads(req.read().decode())
    except Exception as e:
        print(f"Error connecting to Chrome: {e}")
        return

    flow_tab = None
    for tab in tabs:
        if "flow.google.com" in tab.get("url", ""):
            flow_tab = tab
            break

    if not flow_tab:
        print("No Flow tab found!")
        return

    ws_url = flow_tab["webSocketDebuggerUrl"]
    print(f"Connecting to: {ws_url}")

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        async def call_cdp(method, params=None):
            cid = int(asyncio.get_event_loop().time() * 1000) % 1000000
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    msg = json.loads(raw)
                    if msg.get("id") == cid:
                        return msg.get("result", {})
                except asyncio.TimeoutError:
                    return None

        # 1. Take a screenshot
        shot = await call_cdp("Page.captureScreenshot", {"format": "png"})
        if shot and "data" in shot:
            artifact_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
            shot_path = os.path.join(artifact_dir, "flow_live_state.png")
            with open(shot_path, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print(f"Saved screenshot to {shot_path}")

        # 2. Check DOM state
        dom_check_js = """
        (() => {
            const textNodes = Array.from(document.querySelectorAll('*'))
                .filter(el => el.children.length === 0 && (el.innerText || '').trim().length > 0)
                .map(el => (el.innerText || '').trim());
            
            // Check for Genehmigen / cost card
            const approveBtn = Array.from(document.querySelectorAll('button, div.option-row, div[role="button"]'))
                .find(el => {
                    const t = (el.innerText || '').trim();
                    return t === 'Genehmigen' || t === 'Сгенерировать' || t.startsWith('Genehmigen') || t.startsWith('Bestätigen') || t === 'Approve';
                });
            let approveClicked = false;
            if (approveBtn) {
                (approveBtn.closest('button') || approveBtn.closest('div.option-row') || approveBtn).click();
                approveClicked = true;
            }

            // Check for videos
            const videos = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.src || v.currentSrc,
                duration: v.duration,
                paused: v.paused
            }));

            // Check for progress indicators / spinners
            const progressTexts = textNodes.filter(t => 
                t.includes('%') || 
                t.toLowerCase().includes('generier') || 
                t.toLowerCase().includes('wird') || 
                t.toLowerCase().includes('verbleibend') ||
                t.toLowerCase().includes('wart') ||
                t.toLowerCase().includes('error') ||
                t.toLowerCase().includes('abgebrochen') ||
                t.toLowerCase().includes('timeout')
            );

            // Last 15 visible text items in chat/history
            const chatCards = Array.from(document.querySelectorAll('.agent-panel-history, [class*="chat"], [class*="message"], [class*="card"]'))
                .slice(-5)
                .map(c => (c.innerText || '').slice(0, 200));

            return {
                approveClicked,
                approveFound: !!approveBtn,
                videoCount: videos.length,
                videos,
                progressTexts: progressTexts.slice(-10),
                recentChatText: chatCards
            };
        })()
        """
        dom_res = await call_cdp("Runtime.evaluate", {"expression": dom_check_js, "returnByValue": True})
        val = dom_res.get("result", {}).get("value", {}) if dom_res else {}
        print("DOM State Result:")
        print(json.dumps(val, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
