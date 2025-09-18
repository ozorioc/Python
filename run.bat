@echo off
set PORT=%1
if "%PORT%"=="" set PORT=8501
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" -Port %PORT%

