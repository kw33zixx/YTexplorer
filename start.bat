@echo off
echo Starting YouTube's Trash Bin Web Explorer...
cd /d "%~dp0"
py -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause
