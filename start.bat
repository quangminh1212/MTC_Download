@echo off
title MeTruyenCV Downloader

echo MeTruyenCV Downloader
echo ====================

pip install -r requirements.txt >nul 2>&1

if not exist "downloads" mkdir downloads

echo Starting application...
echo Open: http://localhost:5000

timeout /t 2 /nobreak >nul
start http://localhost:5000

python app.py

pause
