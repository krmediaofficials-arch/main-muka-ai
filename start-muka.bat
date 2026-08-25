@echo off
cd /d C:\Users\Kashmiikaa\Desktop\main-muka-ai

call .venv\Scripts\activate.bat

powershell -Command "if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) { Start-Process cmd -ArgumentList '/k','cd /d C:\Users\Kashmiikaa\Desktop\main-muka-ai && call .venv\Scripts\activate.bat && python -m uvicorn main:app --port 8000' }"

powershell -Command "if (-not (Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue)) { Start-Process cmd -ArgumentList '/k','cd /d C:\Users\Kashmiikaa\Desktop\main-muka-ai && call .venv\Scripts\activate.bat && python client_ui.py' }"

exit