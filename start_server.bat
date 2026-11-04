@echo off
cd /d D:\Projects\VideoGenerator
set AGNES_RATE_LIMIT=6
set AGNES_VIDEO_QUEUE_RETRY_SECONDS=3600
.venv\Scripts\python.exe server.py > server_run8.log 2>&1
