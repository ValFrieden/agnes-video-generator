# -*- coding: utf-8 -*-
"""Direct submit of one i2v task to Agnes upstream (no local server needed).
Usage: python direct_submit.py <image.png> <seconds 4-12> <name> <prompt>
Appends: <name> <video_id> to direct.log. Idempotent per name.
"""
import base64, json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
KEY = ""
with open(os.path.join(os.path.dirname(ROOT), ".env"), encoding="utf-8") as f:
    for line in f:
        if line.startswith("AGNES_API_KEY="):
            KEY = line.split("=", 1)[1].strip()
            break
BASE = "https://apihub.agnes-ai.com"
V1 = BASE + "/v1"
MODEL = "agnes-video-2.5-flash"
HDR = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

image_path, seconds, name, prompt = sys.argv[1], str(max(4, min(int(sys.argv[2]), 12))), sys.argv[3], sys.argv[4]
log_path = os.path.join(ROOT, "direct.log")
done = set()
if os.path.exists(log_path):
    with open(log_path, encoding="utf-8") as f:
        done = {line.split()[0] for line in f if line.strip()}
if name in done:
    print(f"{name} already in direct.log")
    sys.exit(0)

with open(image_path, "rb") as f:
    b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()
up = {
    "model": "agnes-image-2.5-flash",
    "prompt": "Keep the image exactly as it is",
    "n": 1, "size": "1024x1024",
    "extra_body": {"response_format": "url", "image": b64},
}
import requests
r = requests.post(V1 + "/images/generations", headers=HDR, json=up, timeout=(30, 180))
r.raise_for_status()
url = r.json()["data"][0]["url"]
print(f"{name} uploaded -> {url[:70]}...")

payload = {
    "model": MODEL, "prompt": prompt, "mode": "reference", "images": [url],
    "seconds": seconds, "size": "720P", "aspect_ratio": "16:9",
}
import time
attempt = 0
while True:
    attempt += 1
    r = requests.post(V1 + "/videos", headers=HDR, json=payload, timeout=(30, 120))
    if r.status_code == 200:
        break
    print(f"{name} attempt {attempt}: {r.status_code} {r.text[:120]}", flush=True)
    if r.status_code in (400, 401, 403, 422):
        sys.exit(1)
    time.sleep(75)  # polite retry: queue_full / 5xx / 429
vid = r.json().get("video_id") or r.json().get("id")
with open(log_path, "a", encoding="utf-8") as f:
    f.write(f"{name} {vid}\n")
print(f"{name} submitted {vid} after {attempt} attempts")
