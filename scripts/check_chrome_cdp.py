import subprocess
import requests
import json

try:
    r = requests.get('http://127.0.0.1:9222/json/version', timeout=2)
    print("CDP ALIVE:", r.json())
except Exception as e:
    print("CDP NOT REACHABLE:", e)

# Check running processes
try:
    out = subprocess.check_output(['powershell', '-Command', "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Select-Object ProcessId, CommandLine | Out-String -Width 400"], encoding='utf-8', errors='ignore')
    for line in out.splitlines():
        if 'remote-debugging' in line or 'User Data Flow' in line:
            print("MATCH:", line[:250])
except Exception as e:
    print("Error checking processes:", e)
