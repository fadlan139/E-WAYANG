@echo off
setlocal
cd /d "%~dp0"
set "PY311=C:\Users\labta\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PY311%" (
  echo [ERROR] Python 3.11 tidak ditemukan.
  pause
  exit /b 1
)

"%PY311%" main.py --projector
pause
