import subprocess
import os
import time
import requests

chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
profile_dir = r"C:\Users\Valeri\AppData\Local\Google\Chrome\User Data Flow"

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

cmd = [
    chrome_exe,
    "--remote-debugging-port=9222",
    f"--user-data-dir={profile_dir}",
    "https://flow.google.com"
]

print("Launching detached:", cmd)
proc = subprocess.Popen(
    cmd,
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
    close_fds=True
)
print("PID:", proc.pid)

for i in range(15):
    time.sleep(1)
    try:
        r = requests.get('http://127.0.0.1:9222/json/version', timeout=1)
        print("CDP SUCCESS:", r.json().get('Browser'))
        break
    except Exception:
        print(f"Waiting... ({i+1})")
