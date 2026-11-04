import json, sys, urllib.request

ids = sys.argv[1:]
for tid in ids:
    try:
        with urllib.request.urlopen(f"http://localhost:8765/api/tasks/{tid}", timeout=30) as r:
            t = json.load(r).get("task", {})
        print(tid, "|", t.get("status"), "|", t.get("current_step"), "|", str(t.get("current_message"))[:150])
    except Exception as e:
        print(tid, "| ERROR", e)
