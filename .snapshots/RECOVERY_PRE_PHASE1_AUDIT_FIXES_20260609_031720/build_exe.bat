@echo off
title Universal Clipboard - Build .exe
echo ============================================
echo  Universal Clipboard - Building .exe
echo ============================================
echo.

:: Install/upgrade PyInstaller
echo [1/3] Installing PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)

:: Install app dependencies
echo [2/3] Installing app dependencies...
pip install pyperclip pystray aiohttp cryptography Pillow pynput --quiet

:: Build the exe
echo [3/3] Building UniversalClipboard.exe ...
pyinstaller build_exe.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed! See output above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  SUCCESS! Your .exe is ready:
echo  dist\UniversalClipboard.exe
echo ============================================
echo.
pause
