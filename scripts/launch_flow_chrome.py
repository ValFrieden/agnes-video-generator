import subprocess
import os
import time
import requests

chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
profile_dir = r"C:\Users\Valeri\AppData\Local\Google\Chrome\User Data Flow"
os.makedirs(profile_dir, exist_ok=True)

project_url = "https://flow.google.com/project/d7aa8d17-a219-4cf4-b840-832427562b58"

cmd = [
    chrome_exe,
    "--remote-debugging-port=9222",
    f"--user-data-dir={profile_dir}",
    "--no-first-run",
    "--no-default-browser-check",
    project_url
]

print("Launching detached Chrome on port 9222...")
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
proc = subprocess.Popen(
    cmd,
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
    close_fds=True
)
print("Launched Chrome PID:", proc.pid)

for i in range(15):
    time.sleep(1)
    try:
        r = requests.get('http://127.0.0.1:9222/json/version', timeout=1)
        print("CDP SUCCESS:", r.json().get("Browser"))
        break
    except Exception:
        print(f"Waiting for CDP... ({i+1}/15)")
