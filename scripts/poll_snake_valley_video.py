import asyncio
import json
import urllib.request
import websockets
import os
import time

EXISTING_SRCS = {
    "https://flow.google.com/asb/ANqvLObSPpLqwAfotSlHg4bq2CnxDwPBJjIRUZ0pOolVJTQoWWzzYUHSSN_z4R_YaSflGxzMYZVhQgj2IZ1y26GATyYUr7HqrxqBdWHIj5uLiYb-Mkqdh6r5-qoQ7hqODCAkKX5qrgxoehNc_rAfdUk052_unHTem2bat60O8nO-8Q=mm,22,15",
    "https://flow.google.com/asb/ANqvLObCXid6DY4kbAMEOuZbHxYYNJSs61LFYGILpQZoY-2L7iodBxqeq8WTLeBL9lHGsyFejej-tUKt09o9v0STzpDkSjd37yccnJM0VpfqpRVrbtJitCGvHVl07xrVcehkOUVpv9_A1Pb2UZMNyspN73-SIg-tV98jNgKu7Rh-2A=mm,22,15",
    "https://flow.google.com/asb/ANqvLOaE7NWrc3Z6d_F14BaHqsIopRHnQlpRAShG3a_i5EZc5xjL-36SU-AvFAAthfXLgnx3PDTGABImqNvPyhGrTsqO5xuMVpNVWQYrg2ai2USuUo0yzLHw59fIHoNAbZl9SBif_-p3Tgdd23fgnffjHzCk-_cGHqe1kKr45Ps19g=mm,22,15",
    "https://flow.google.com/asb/ANqvLObfD1Uj-0T8MXaNgecq2dMpw1SuD1rAFwCvPaqzHKhCHKYLNE6WXufuCIod1C2h_lYBvoHiVx_ETYa3sLYCxoWNMAWY-38j87MeLN1EW5RvQtt44K81ZxuvSzAbPDfI9IBBTQ99unZ1D9L2qEVBtYC-FD8IQqZ_MxQzdQazDg=mm,22,15",
    "https://flow.google.com/asb/ANqvLOZZIcqOCn3mHdssa1w4cHOp6gy9MTSzyaxDZ6WcQCJ9BbdVuXZkp1cSkgXHzqQvW9BkgCPvm9Z-ptzrKpSSP1vyeWZbuDGtv1L-Ii5gI0upFra34O5v5-1W1Veo2wIN5ABX9jZ0yfZcL7lVUzJ5UM9L3wnVfGHUYRcPIdN0Vg=mm,22,15"
}

async def poll_video():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    ws_url = flow_tab["webSocketDebuggerUrl"]

    print("Polling Google Flow for completed video...", flush=True)

    check_js = """
    (() => {
        const videos = Array.from(document.querySelectorAll('video')).map(v => ({
            src: v.src || v.currentSrc,
            duration: v.duration,
            ready: v.readyState
        }));

        // Check if there is any progress percentage or status in chat
        const chatText = document.body.innerText;
        const matchPercent = chatText.match(/(\\d+)\\s*%/);
        const percent = matchPercent ? matchPercent[1] : null;

        // Check cards in chat
        const lastChat = chatText.slice(-600);

        return {
            videos,
            percent,
            hasStartedMsg: lastChat.includes('started generating'),
            lastChatSnippet: lastChat.slice(-250)
        };
    })()
    """

    for iteration in range(60): # up to 10 minutes
        try:
            async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
                cid = 200 + iteration
                await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": check_js, "returnByValue": True}}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                res = json.loads(raw).get("result", {}).get("result", {}).get("value", {})
                
                videos = res.get("videos", [])
                new_videos = [v for v in videos if v["src"] and v["src"] not in EXISTING_SRCS]
                
                print(f"[{time.strftime('%H:%M:%S')}] Check #{iteration+1}: Total videos={len(videos)}, New={len(new_videos)}, Percent={res.get('percent')}%", flush=True)

                if new_videos:
                    target_video = new_videos[-1]
                    print(f">>> FOUND NEW VIDEO: {target_video['src']}", flush=True)
                    return target_video["src"]

                # If no new video yet, wait 10s
        except Exception as e:
            print(f"Iteration error: {e}", flush=True)

        await asyncio.sleep(10)

    return None

if __name__ == "__main__":
    video_url = asyncio.run(poll_video())
    if video_url:
        print(f"SUCCESS_VIDEO_URL: {video_url}")
    else:
        print("POLL_TIMEOUT")
