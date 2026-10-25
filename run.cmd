@echo off
chcp 65001 >nul
rem One-click launcher: middleware + app (real work in tools\run.ps1)
setlocal
set "ROOT=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%tools\run.ps1"
if errorlevel 1 pause
