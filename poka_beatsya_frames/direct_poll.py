# -*- coding: utf-8 -*-
"""Direct poll/download of i2v tasks submitted via direct_submit.py.
Usage: python direct_poll.py
For each '<name> <video_id>' in direct.log without clips2/<name>.mp4:
poll upstream; on completed -> download to clips2/<name>.mp4.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
KEY = ""
with open(os.path.join(os.path.dirname(ROOT), ".env"), encoding="utf-8") as f:
    for line in f:
        if line.startswith("AGNES_API_KEY="):
            KEY = line.split("=", 1)[1].strip()
            break
BASE = "https://apihub.agnes-ai.com"
HDR = {"Authorization": f"Bearer {KEY}"}
CLIPS = os.path.join(ROOT, "clips2")
os.makedirs(CLIPS, exist_ok=True)

import requests

log_path = os.path.join(ROOT, "direct.log")
if not os.path.exists(log_path):
    print("direct.log missing")
    sys.exit(0)
pending = 0
with open(log_path, encoding="utf-8") as f:
    entries = [line.split() for line in f if line.strip()]
for name, vid in entries:
    out = os.path.join(CLIPS, name + ".mp4")
    if os.path.exists(out):
        continue
    r = requests.get(BASE + "/agnesapi",
                     params={"video_id": vid, "model_name": "agnes-video-2.5-flash"},
                     headers=HDR, timeout=(15, 60))
    if r.status_code == 404:
        print(f"{name}: not yet visible (404)")
        pending += 1
        continue
    if r.status_code != 200:
        print(f"{name}: HTTP {r.status_code}")
        pending += 1
        continue
    res = r.json()
    status = (res.get("status") or "").lower()
    if status in ("completed",):
        url = (res.get("video_url") or res.get("url")
               or (res.get("data") or {}).get("video_url")
               or (res.get("data") or {}).get("url"))
        if not url:
            print(f"{name}: completed but no URL: {json.dumps(res)[:200]}")
            pending += 1
            continue
        d = requests.get(url, timeout=(30, 300))
        with open(out, "wb") as f:
            f.write(d.content)
        print(f"{name}: DONE {len(d.content)//1024}KB")
    elif status in ("failed",):
        print(f"{name}: FAILED {json.dumps(res)[:200]}")
    else:
        print(f"{name}: {status or 'unknown'}")
        pending += 1
print(f"pending: {pending}")
