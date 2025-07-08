@echo off
chcp 65001 >nul
title Commit MeTruyenCV Web Interface

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              Commit MeTruyenCV Web Interface                 ║
echo ║                  Tự động commit tất cả                      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git không được tìm thấy!
    echo 💡 Vui lòng cài đặt Git để sử dụng tính năng này
    pause
    exit /b 1
)

:: Check if this is a git repository
if not exist ".git" (
    echo ❓ Đây không phải Git repository. Bạn có muốn khởi tạo? (y/n)
    set /p INIT_GIT=
    if /i "!INIT_GIT!"=="y" (
        git init
        echo ✅ Git repository đã được khởi tạo
    ) else (
        echo ❌ Hủy commit
        pause
        exit /b 0
    )
)

:: Show current status
echo 📋 Git status hiện tại:
git status --short

echo.
echo 📁 Files sẽ được commit:
echo    ✅ Web Interface (app.py, web_downloader.py)
echo    ✅ Templates (base.html, index.html, config.html, download.html, logs.html, performance.html, error.html)
echo    ✅ Static Assets (CSS, JS, images, manifest)
echo    ✅ Setup Scripts (setup_web.bat/sh, run_web.bat, update_web.bat, uninstall_web.bat)
echo    ✅ System Tools (check_system.py)
echo    ✅ Requirements (requirements_web.txt)
echo    ✅ Documentation (README files)
echo.

set /p CONFIRM="❓ Bạn có muốn commit tất cả thay đổi? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo ✅ Hủy commit
    pause
    exit /b 0
)

:: Add all web interface files
echo 📦 Thêm files vào staging...

:: Core web files
git add app.py
git add web_downloader.py
git add requirements_web.txt

:: Templates
git add templates/
git add templates/*.html

:: Static assets
git add static/
git add static/css/
git add static/js/
git add static/img/
git add static/manifest.json

:: Setup and management scripts
git add setup_web.bat
git add setup_web.sh
git add run_web.bat
git add update_web.bat
git add uninstall_web.bat
git add check_system.py

:: Documentation
git add README_COMPLETE.md
git add WEB_INTERFACE_README.md

:: Config files (if they exist and user wants them)
if exist "config.txt" (
    set /p ADD_CONFIG="📝 Thêm config.txt vào commit? (y/n): "
    if /i "!ADD_CONFIG!"=="y" (
        git add config.txt
        echo ✅ config.txt đã được thêm
    )
)

echo ✅ Files đã được thêm vào staging

:: Create commit message
echo.
echo 📝 Tạo commit message...

set COMMIT_MSG="🌐 Add complete MeTruyenCV Web Interface

✨ Features:
- 📊 Dashboard với real-time status
- 📥 Download Manager với progress tracking  
- ⚙️ Configuration Manager với backup/restore
- 📋 Log Viewer với filtering và search
- 📊 Performance Monitor với system stats
- 🎨 Modern responsive UI với Bootstrap 5
- 🔄 Real-time WebSocket updates
- 📱 PWA support với manifest
- 🛠️ Complete setup và management scripts

🔧 Technical:
- Flask + Flask-SocketIO backend
- WebSocket real-time communication
- In-memory caching system
- Performance monitoring
- Error handling và logging
- Mobile responsive design
- Auto-setup scripts

📁 Files:
- Web app: app.py, web_downloader.py
- Templates: base.html, index.html, config.html, download.html, logs.html, performance.html, error.html
- Assets: custom.css, utils.js, favicon.svg, logo.svg, manifest.json
- Scripts: setup_web.bat/sh, run_web.bat, update_web.bat, uninstall_web.bat, check_system.py
- Docs: README_COMPLETE.md, WEB_INTERFACE_README.md

🎯 Ready for production use!"

:: Commit changes
echo 💾 Đang commit...
git commit -m %COMMIT_MSG%

if errorlevel 1 (
    echo ❌ Lỗi khi commit!
    echo 💡 Kiểm tra git status và thử lại
    pause
    exit /b 1
)

echo ✅ Commit thành công!

:: Show commit info
echo.
echo 📋 Thông tin commit:
git log --oneline -1

:: Ask about remote push
echo.
set /p PUSH_REMOTE="🚀 Bạn có muốn push lên remote repository? (y/n): "
if /i "%PUSH_REMOTE%"=="y" (
    echo 📡 Đang push lên remote...
    
    :: Check if remote exists
    git remote -v | findstr origin >nul
    if errorlevel 1 (
        echo ⚠️  Chưa có remote repository
        set /p REMOTE_URL="🔗 Nhập URL remote repository: "
        if not "!REMOTE_URL!"=="" (
            git remote add origin !REMOTE_URL!
            echo ✅ Remote đã được thêm
        ) else (
            echo ❌ Không có URL, bỏ qua push
            goto :end
        )
    )
    
    :: Push to remote
    git push -u origin main 2>nul || git push -u origin master 2>nul
    if errorlevel 1 (
        echo ❌ Lỗi khi push!
        echo 💡 Kiểm tra remote URL và quyền truy cập
    ) else (
        echo ✅ Push thành công!
    )
) else (
    echo ✅ Chỉ commit local
)

:end
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    COMMIT HOÀN TẤT!                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 MeTruyenCV Web Interface đã được commit thành công!
echo.
echo 📋 Tóm tắt:
echo    ✅ Tất cả web interface files đã được commit
echo    ✅ Commit message chi tiết đã được tạo
echo    ✅ Repository đã được cập nhật
echo.
echo 🚀 Tiếp theo:
echo    - Chạy web interface: run_web.bat
echo    - Kiểm tra tại: http://localhost:5000
echo    - Đọc docs: README_COMPLETE.md
echo.

pause
