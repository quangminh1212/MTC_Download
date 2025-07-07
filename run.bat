@echo off
setlocal enabledelayedexpansion

REM Kiểm tra môi trường ảo đã tồn tại chưa
if not exist "venv" (
    echo [LỖI] Môi trường ảo chưa được thiết lập.
    echo Vui lòng chạy setup.bat trước để thiết lập môi trường.
    pause
    exit /b 1
)

REM Kích hoạt môi trường ảo
call venv\Scripts\activate

REM Kiểm tra tham số đầu vào
set "mode=%1"
if "%mode%"=="" set "mode=web"

if "%mode%"=="web" (
    echo ===== KHỞI CHẠY ỨNG DỤNG WEB =====
    echo Truy cập ứng dụng tại http://localhost:3000
    python -m mtc_downloader.cli web
) else if "%mode%"=="gui" (
    echo ===== KHỞI CHẠY ỨNG DỤNG GIAO DIỆN ĐỒ HỌA =====
    python -m mtc_downloader.cli gui
) else if "%mode%"=="cli" (
    echo ===== KHỞI CHẠY ỨNG DỤNG DÒNG LỆNH =====
    echo Hướng dẫn sử dụng:
    mtc-download --help
    echo.
    echo Ví dụ:
    echo mtc-download https://metruyencv.com/truyen/ten-truyen/chuong-XX
    echo mtc-extract -i file.html
    echo.
    cmd /k
) else (
    echo [LỖI] Tham số không hợp lệ: %mode%
    echo Các tham số hợp lệ: web, gui, cli
    pause
    exit /b 1
)

REM Thoát khỏi môi trường ảo nếu không phải chế độ CLI
if not "%mode%"=="cli" (
    call venv\Scripts\deactivate
) 