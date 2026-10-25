@echo off
chcp 65001 >nul
rem Day 1 one-click: middleware + app + self-check (logic in tools\day1.ps1)
setlocal
set "ROOT=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%tools\day1.ps1"
