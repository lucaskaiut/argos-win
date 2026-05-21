@echo off
REM Argos — iniciar com duplo clique ou: run.bat
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
if errorlevel 1 pause
