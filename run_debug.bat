@echo off
setlocal
cd /d "%~dp0"
set "PY311=C:\Users\labta\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PY311%" (
  echo [ERROR] Python 3.11 tidak ditemukan.
  echo %PY311%
  pause
  exit /b 1
)

echo Menjalankan Bima dan Arjuna...
"%PY311%" main.py
echo.
echo Program selesai dengan kode %ERRORLEVEL%.
pause
