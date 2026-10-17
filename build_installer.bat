@echo off
title Universal Clipboard - Build Windows Installer
echo ========================================================
echo   Universal Clipboard - Building Windows Setup Installer
echo ========================================================
echo.

set "ISCC="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo ERROR: Inno Setup 6 compiler (ISCC.exe) not found.
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo [1/2] Compiling Inno Setup script with:
echo "%ISCC%"
"%ISCC%" "installer\UniversalClipboard.iss"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Inno Setup compilation failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Signing binaries with BAZIQHUE Authenticode...
powershell -ExecutionPolicy Bypass -File "scripts\sign_windows_binaries.ps1"

echo.
echo ========================================================
echo  SUCCESS! Signed installer ready:
echo  dist\UniversalClipboard-Setup-1.1.0.exe
echo ========================================================
echo.
pause
