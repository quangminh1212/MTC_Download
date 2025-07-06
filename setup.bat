@echo off
setlocal enabledelayedexpansion

echo ===================================
echo THIẾT LẬP MÔI TRƯỜNG MTC_DOWNLOAD
echo ===================================
echo.

REM Kiểm tra Python đã được cài đặt chưa
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Python chưa được cài đặt. Vui lòng cài đặt Python từ https://www.python.org/downloads/
    echo Đảm bảo đánh dấu vào "Add Python to PATH" trong quá trình cài đặt.
    pause
    exit /b 1
)

echo [OK] Đã phát hiện Python.
echo.

echo ===================================
echo CÀI ĐẶT CÁC GÓI PYTHON CẦN THIẾT
echo ===================================
echo.

echo Đang cài đặt các gói Python...
pip install httpx beautifulsoup4 ebooklib async-lru backoff playwright pytesseract Pillow appdirs tqdm lxml

if %errorlevel% neq 0 (
    echo [LỖI] Không thể cài đặt các gói Python. Vui lòng kiểm tra kết nối internet và thử lại.
    pause
    exit /b 1
)

echo [OK] Đã cài đặt các gói Python thành công.
echo.

echo ===================================
echo CÀI ĐẶT TRÌNH DUYỆT CHO PLAYWRIGHT
echo ===================================
echo.

echo Đang cài đặt trình duyệt Firefox cho Playwright...
python -m playwright install firefox

if %errorlevel% neq 0 (
    echo [LỖI] Không thể cài đặt trình duyệt cho Playwright.
    pause
    exit /b 1
)

echo [OK] Đã cài đặt trình duyệt Firefox cho Playwright thành công.
echo.

echo ===================================
echo TẢI VÀ CÀI ĐẶT TESSERACT OCR
echo ===================================
echo.

REM Kiểm tra xem thư mục Tesseract-OCR đã tồn tại chưa
if exist "%~dp0\Tesseract-OCR\tesseract.exe" (
    echo [OK] Tesseract OCR đã được cài đặt trước đó.
) else (
    echo Đang tải Tesseract OCR (có thể mất vài phút)...
    
    REM Sử dụng PowerShell để tải xuống Tesseract
    powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe' -OutFile 'tesseract-installer.exe'}"
    
    if %errorlevel% neq 0 (
        echo [LỖI] Không thể tải Tesseract OCR. Vui lòng tải thủ công từ:
        echo https://github.com/UB-Mannheim/tesseract/wiki
        echo Sau đó cài đặt vào thư mục "Tesseract-OCR" trong thư mục dự án này.
        pause
        exit /b 1
    )
    
    echo Đang cài đặt Tesseract OCR...
    echo LƯU Ý: Trong quá trình cài đặt, hãy đảm bảo:
    echo 1. Chọn "Vietnamese" trong danh sách ngôn ngữ (Additional language data)
    echo 2. Đổi đường dẫn cài đặt thành: "%~dp0\Tesseract-OCR"
    echo.
    echo Bấm phím bất kỳ để bắt đầu cài đặt Tesseract...
    pause > nul
    
    start /wait tesseract-installer.exe
    
    if not exist "%~dp0\Tesseract-OCR\tesseract.exe" (
        echo.
        echo [CẢNH BÁO] Không tìm thấy Tesseract OCR tại đường dẫn dự kiến.
        echo Nếu bạn đã cài đặt Tesseract vào thư mục khác, vui lòng sửa đường dẫn sau trong file main.py:
        echo pytesseract.pytesseract.tesseract_cmd = fr'{file_location}\Tesseract-OCR\tesseract.exe'
    ) else (
        echo [OK] Đã cài đặt Tesseract OCR thành công.
        del tesseract-installer.exe
    )
)

echo.
echo ===================================
echo THIẾT LẬP HOÀN TẤT
echo ===================================
echo.
echo Đã cài đặt thành công tất cả các thành phần cần thiết!
echo.
echo Để chạy chương trình, sử dụng lệnh: python main.py
echo.
echo THÔNG TIN BỔ SUNG:
echo - Đường dẫn URL phải ở dạng metruyencv.info (không phải .com)
echo - Nếu gặp lỗi EOFError, hãy sử dụng Command Prompt tiêu chuẩn thay vì PowerShell
echo - File EPUB sẽ được lưu trong thư mục C:/novel hoặc D:/novel (tùy cấu hình)
echo.
pause 