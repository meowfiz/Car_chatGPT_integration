@echo off
rem Leaving the office: lock the session and kill the monitors. The bridge keeps running.
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0blank_screen.ps1"
