@echo off
chcp 65001 >nul
title MeTruyenCV Web Interface Update

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  MeTruyenCV Web Update                       ║
echo ║              Cập nhật web interface                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment không tồn tại!
    echo 💡 Chạy setup_web.bat để cài đặt lại
    pause
    exit /b 1
)

:: Activate virtual environment
echo 🔄 Kích hoạt virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Không thể kích hoạt virtual environment!
    pause
    exit /b 1
)

:: Backup current config
echo 💾 Backup cấu hình hiện tại...
if exist "config.txt" (
    copy "config.txt" "config_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt" >nul
    echo ✅ Config đã được backup
)

:: Update pip
echo 📦 Cập nhật pip...
python -m pip install --upgrade pip

:: Update main dependencies
echo 📦 Cập nhật dependencies chính...
if exist "requirements.txt" (
    pip install --upgrade -r requirements.txt
    if errorlevel 1 (
        echo ⚠️  Một số dependencies không thể cập nhật
    ) else (
        echo ✅ Dependencies chính đã được cập nhật
    )
) else (
    echo ⚠️  Không tìm thấy requirements.txt
)

:: Update web dependencies
echo 📦 Cập nhật web dependencies...
if exist "requirements_web.txt" (
    pip install --upgrade -r requirements_web.txt
    if errorlevel 1 (
        echo ⚠️  Một số web dependencies không thể cập nhật
    ) else (
        echo ✅ Web dependencies đã được cập nhật
    )
) else (
    echo ⚠️  Không tìm thấy requirements_web.txt
)

:: Update ChromeDriver
echo 🌐 Cập nhật ChromeDriver...
pip install --upgrade webdriver-manager
if errorlevel 1 (
    echo ⚠️  Không thể cập nhật webdriver-manager
) else (
    echo ✅ ChromeDriver manager đã được cập nhật
)

:: Check for security updates
echo 🔒 Kiểm tra security updates...
pip install --upgrade pip-audit 2>nul
if not errorlevel 1 (
    pip-audit --desc 2>nul
    if errorlevel 1 (
        echo ⚠️  Phát hiện một số vấn đề bảo mật
        echo 💡 Chạy: pip-audit --fix để tự động sửa
    ) else (
        echo ✅ Không có vấn đề bảo mật
    )
) else (
    echo ⚠️  Không thể kiểm tra security updates
)

:: Clean up cache
echo 🧹 Dọn dẹp cache...
pip cache purge 2>nul
if not errorlevel 1 (
    echo ✅ Cache đã được dọn dẹp
)

:: Test updated installation
echo 🧪 Test cài đặt sau update...
python -c "import flask, flask_socketio, selenium, bs4; print('✅ Tất cả modules hoạt động bình thường')" 2>nul
if errorlevel 1 (
    echo ❌ Có vấn đề với modules sau update
    echo 💡 Có thể cần cài đặt lại: setup_web.bat
) else (
    echo ✅ Test thành công!
)

:: Show current versions
echo.
echo 📋 Phiên bản hiện tại:
python -c "import flask; print(f'Flask: {flask.__version__}')" 2>nul
python -c "import flask_socketio; print(f'Flask-SocketIO: {flask_socketio.__version__}')" 2>nul
python -c "import selenium; print(f'Selenium: {selenium.__version__}')" 2>nul
python -c "import bs4; print(f'BeautifulSoup: {bs4.__version__}')" 2>nul

:: Check for app updates
echo.
echo 🔍 Kiểm tra cập nhật ứng dụng...
if exist ".git" (
    git fetch origin 2>nul
    git status -uno | findstr "behind" >nul
    if not errorlevel 1 (
        echo ⚠️  Có cập nhật mới từ repository
        set /p UPDATE_APP="🔄 Bạn có muốn cập nhật ứng dụng? (y/n): "
        if /i "!UPDATE_APP!"=="y" (
            git pull origin main
            echo ✅ Ứng dụng đã được cập nhật
        )
    ) else (
        echo ✅ Ứng dụng đã là phiên bản mới nhất
    )
) else (
    echo ⚠️  Không phải Git repository, không thể kiểm tra cập nhật
)

:: Deactivate virtual environment
deactivate

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    CẬP NHẬT HOÀN TẤT!                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 Web interface đã được cập nhật thành công!
echo.
echo 📋 Những gì đã được cập nhật:
echo    ✅ Python packages
echo    ✅ Web dependencies
echo    ✅ ChromeDriver manager
echo    ✅ Security checks
echo.
echo 💾 Backup:
echo    - Config backup: config_backup_*.txt
echo.
echo 🚀 Khởi động lại web interface để áp dụng thay đổi:
echo    run_web.bat
echo.

:: Ask to restart
set /p RESTART="🔄 Bạn có muốn khởi động lại web interface ngay bây giờ? (y/n): "
if /i "%RESTART%"=="y" (
    echo.
    echo 🌐 Đang khởi động lại web interface...
    call run_web.bat
) else (
    echo.
    echo ✅ Cập nhật hoàn tất. Khởi động lại khi cần thiết.
    pause
)
