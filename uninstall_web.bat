@echo off
chcp 65001 >nul
title MeTruyenCV Web Interface Uninstall

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                MeTruyenCV Web Uninstall                      ║
echo ║              Gỡ cài đặt web interface                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo ⚠️  CẢNH BÁO: Script này sẽ xóa toàn bộ web interface!
echo.
echo 📋 Những gì sẽ được xóa:
echo    - Virtual environment (venv/)
echo    - Web dependencies
echo    - Log files
echo    - Temporary files
echo    - Desktop shortcuts
echo.
echo 💾 Những gì sẽ được GIỮ LẠI:
echo    - config.txt (cấu hình)
echo    - Downloaded novels
echo    - Source code files
echo.

set /p CONFIRM="❓ Bạn có chắc muốn gỡ cài đặt? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo ✅ Hủy gỡ cài đặt
    pause
    exit /b 0
)

echo.
echo 🗑️  Bắt đầu gỡ cài đặt...

:: Stop any running processes
echo 🛑 Dừng các tiến trình đang chạy...
taskkill /f /im python.exe 2>nul
taskkill /f /im pythonw.exe 2>nul

:: Remove virtual environment
if exist "venv" (
    echo 🗂️  Xóa virtual environment...
    rmdir /s /q venv
    if exist "venv" (
        echo ⚠️  Không thể xóa hoàn toàn venv, có thể do file đang được sử dụng
    ) else (
        echo ✅ Virtual environment đã được xóa
    )
) else (
    echo ⚠️  Virtual environment không tồn tại
)

:: Remove log files
echo 📝 Xóa log files...
if exist "web_app.log" (
    del "web_app.log"
    echo ✅ web_app.log đã được xóa
)

if exist "download.log" (
    del "download.log"
    echo ✅ download.log đã được xóa
)

:: Remove temporary files
echo 🧹 Xóa temporary files...
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo ✅ __pycache__ đã được xóa
)

if exist "*.pyc" (
    del *.pyc
    echo ✅ .pyc files đã được xóa
)

if exist "system_report.json" (
    del "system_report.json"
    echo ✅ system_report.json đã được xóa
)

:: Remove desktop shortcuts
echo 🖥️  Xóa desktop shortcuts...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\MeTruyenCV Web.lnk
if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo ✅ Desktop shortcut đã được xóa
) else (
    echo ⚠️  Desktop shortcut không tồn tại
)

:: Remove Chrome driver cache (if exists)
echo 🌐 Xóa ChromeDriver cache...
if exist "%USERPROFILE%\.wdm" (
    rmdir /s /q "%USERPROFILE%\.wdm" 2>nul
    echo ✅ ChromeDriver cache đã được xóa
)

:: Ask about config backup
echo.
echo 💾 Xử lý config files...
if exist "config.txt" (
    set /p BACKUP_CONFIG="💾 Bạn có muốn backup config.txt trước khi hoàn tất? (y/n): "
    if /i "!BACKUP_CONFIG!"=="y" (
        copy "config.txt" "config_backup_uninstall_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt" >nul
        echo ✅ Config đã được backup thành config_backup_uninstall_*.txt
    )
    
    set /p DELETE_CONFIG="🗑️  Bạn có muốn xóa config.txt? (y/n): "
    if /i "!DELETE_CONFIG!"=="y" (
        del "config.txt"
        echo ✅ config.txt đã được xóa
    ) else (
        echo ✅ config.txt được giữ lại
    )
) else (
    echo ⚠️  config.txt không tồn tại
)

:: Ask about downloaded novels
echo.
set /p DELETE_NOVELS="🗑️  Bạn có muốn xóa các novel đã tải? (y/n): "
if /i "%DELETE_NOVELS%"=="y" (
    echo 📚 Tìm và xóa downloaded novels...
    
    :: Try to find novel directories from config
    if exist "config.txt" (
        for /f "tokens=2 delims==" %%i in ('findstr "drive" config.txt') do set DRIVE=%%i
        for /f "tokens=2 delims==" %%i in ('findstr "folder" config.txt') do set FOLDER=%%i
        
        if defined DRIVE if defined FOLDER (
            set NOVEL_PATH=!DRIVE!:/!FOLDER!
            if exist "!NOVEL_PATH!" (
                rmdir /s /q "!NOVEL_PATH!" 2>nul
                echo ✅ Downloaded novels đã được xóa từ !NOVEL_PATH!
            )
        )
    )
    
    :: Also check common locations
    if exist "C:\novel" (
        rmdir /s /q "C:\novel" 2>nul
        echo ✅ Downloaded novels đã được xóa từ C:\novel
    )
) else (
    echo ✅ Downloaded novels được giữ lại
)

:: Final cleanup
echo.
echo 🧹 Dọn dẹp cuối cùng...

:: Remove pip cache related to this project
pip cache purge 2>nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  GỠ CÀI ĐẶT HOÀN TẤT!                      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 MeTruyenCV Web Interface đã được gỡ cài đặt!
echo.
echo 📋 Đã xóa:
echo    ✅ Virtual environment
echo    ✅ Log files
echo    ✅ Temporary files
echo    ✅ Desktop shortcuts
echo    ✅ ChromeDriver cache
echo.
echo 💾 Còn lại:
echo    - Source code files
echo    - Setup scripts
if exist "config.txt" echo    - config.txt
if exist "config_backup_*.txt" echo    - Config backups
echo.
echo 💡 Để cài đặt lại, chạy: setup_web.bat
echo.

pause
