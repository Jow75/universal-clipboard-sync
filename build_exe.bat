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
pip install pyperclip pystray aiohttp cryptography Pillow pynput pywin32 qrcode --quiet

:: Build the exe
echo [3/3] Building UniversalClipboard.exe ...
pyinstaller build_exe.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed! See output above.
    pause
    exit /b 1
)

:: Copy to Portable release filename
copy /y dist\UniversalClipboard.exe dist\UniversalClipboard-Portable-1.1.0.exe >nul

:: Sign the binaries if signing script exists
if exist "scripts\sign_windows_binaries.ps1" (
    echo [Optional] Signing binaries with BAZIQHUE Authenticode...
    powershell -ExecutionPolicy Bypass -File "scripts\sign_windows_binaries.ps1"
)

echo.
echo ============================================
echo  SUCCESS! Your signed .exe is ready:
echo  dist\UniversalClipboard.exe
echo  dist\UniversalClipboard-Portable-1.1.0.exe
echo ============================================
echo.
pause
