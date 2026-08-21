@echo off
chcp 65001 >nul
cd /d "%~dp0"
title UXM Report UI
echo 開啟 UXM Report 介面...
echo 這個視窗開著就表示介面在跑。關掉視窗或雙擊「關閉介面.bat」即停止。
echo 瀏覽器：http://127.0.0.1:8765/
echo.
python -m uxm_report ui
pause
