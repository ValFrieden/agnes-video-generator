import subprocess
import json

p = subprocess.run(
    ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process -Filter \"Name = 'chrome.exe'\" | Select-Object ProcessId, CommandLine | ConvertTo-Json -Depth 1"],
    capture_output=True,
    text=True
)

try:
    data = json.loads(p.stdout)
except Exception:
    data = []

if isinstance(data, dict):
    data = [data]

killed = []
for item in data:
    cmd = item.get("CommandLine") or ""
    pid = item.get("ProcessId")
    if "User Data Flow" in cmd and pid:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        killed.append(pid)

print("Killed Flow Chrome PIDs:", killed)
