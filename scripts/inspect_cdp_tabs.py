import requests
import json

try:
    r = requests.get('http://127.0.0.1:9222/json/list', timeout=3)
    tabs = r.json()
    print(f"Open tabs count: {len(tabs)}")
    for t in tabs:
        print(f" - {t.get('title')}: {t.get('url')}")
except Exception as e:
    print("Error connecting to CDP:", e)
