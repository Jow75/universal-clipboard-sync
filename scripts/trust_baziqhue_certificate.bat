@echo off
title Trust BAZIQHUE Publisher Certificate
echo ========================================================
echo   Universal Clipboard Sync - Trust BAZIQHUE Certificate
echo ========================================================
echo.
echo Adding BAZIQHUE Code Signing certificate to your trusted store...
powershell -ExecutionPolicy Bypass -File "%~dp0trust_baziqhue_certificate.ps1"
echo.
pause
