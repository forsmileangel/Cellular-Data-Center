@echo off
chcp 65001 >nul
cd /d "%~dp0"
title UXM Report UI
python -m uxm_report stop
pause
