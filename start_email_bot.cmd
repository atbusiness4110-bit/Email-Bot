@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python auto_reply_bot.py
pause
