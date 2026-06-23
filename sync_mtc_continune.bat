@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════════════════════
:: MTC Continune → Wasabi Sync (High Performance)
:: Target: 80% RAM/CPU utilization, max throughput
:: ═══════════════════════════════════════════════════════════════

set "SOURCE=D:\Dev\MTC_Continune"
set "DEST=wasabi:mtc1212/MTC_Continune"
set "RCLONE=C:\Dev\MTC_Download\rclone\rclone.exe"

echo [INFO] Starting high-performance sync...
echo [INFO] Source: %SOURCE%
echo [INFO] Dest: %DEST%
echo.

"%RCLONE%" sync "%SOURCE%" "%DEST%" ^
  --s3-provider=Wasabi ^
  --s3-endpoint=s3.ap-southeast-1.wasabisys.com ^
  --s3-access-key-id=DSELNA7UIKBXHLWTBUIG ^
  --s3-secret-access-key=Y7J5ycVjzJKtoOClLSUwfPoI1JqP9XHr4KeoB3g7 ^
  --s3-force-path-style ^
  --transfers=32 ^
  --checkers=64 ^
  --buffer-size=512M ^
  --multi-thread-cutoff=100M ^
  --multi-thread-streams=8 ^
  --fast-list ^
  --update ^
  --stats=30s ^
  --stats-one-line ^
  --log-level=INFO ^
  --log-file="sync_mtc_continune.log" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Sync completed
) else (
    echo [ERROR] Sync failed: %ERRORLEVEL%
)

endlocal
