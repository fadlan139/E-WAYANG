@echo off
setlocal
cd /d "%~dp0"

set "PY311=C:\Users\labta\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PY311%" (
    echo [ERROR] Python 3.11 tidak ditemukan:
    echo %PY311%
    echo.
    echo Install Python 3.11 terlebih dahulu.
    pause
    exit /b 1
)

echo ==========================================
echo BIMA DAN ARJUNA - INSTALL DEPENDENCIES
echo Python:
"%PY311%" --version
echo ==========================================
echo.

"%PY311%" -m pip install --upgrade pip
if errorlevel 1 goto :fail

"%PY311%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo INSTALASI BERHASIL
echo ==========================================
echo.
echo Tes library...
"%PY311%" -c "import pygame, cv2, mediapipe, numpy; print('pygame', pygame.version.ver); print('opencv', cv2.__version__); print('mediapipe', mediapipe.__version__); print('numpy', numpy.__version__)"
if errorlevel 1 goto :fail

echo.
echo Semua library siap.
pause
exit /b 0

:fail
echo.
echo [ERROR] Instalasi gagal.
echo Periksa pesan di atas.
pause
exit /b 1
