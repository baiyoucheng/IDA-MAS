@echo off
chcp 65001 >nul
cd /d "E:\WorkBuddy\ida-mas"
echo === IDA-MAS 启动中 ===
echo 浏览器打开 http://localhost:8000
echo.
C:\Users\15210\.workbuddy\binaries\python\envs\ida-mas\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
