@echo off
REM 启动网页版后端（Flask）
cd /d "%~dp0..\web\backend"
python app.py
pause
