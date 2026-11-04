@echo off
set "ROOT=%~dp0"

start "PrintMonitor Backend" /min cmd /k "cd /d ""%ROOT%backend"" && py -m uvicorn main:app --host 0.0.0.0 --port 8000"

start "PrintMonitor Frontend" /min cmd /k "cd /d ""%ROOT%frontend"" && npm.cmd run dev -- --host 0.0.0.0"

exit