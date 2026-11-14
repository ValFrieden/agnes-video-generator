import subprocess
import os
import time

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

print("Starting Chrome process in daemon mode...")
proc = subprocess.Popen(cmd)
print("Chrome PID:", proc.pid)

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
