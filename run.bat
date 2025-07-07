@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION

echo ===================================
echo MTC DOWNLOADER - PHIEN BAN TICH HOP
echo ===================================
echo.

REM Tạo thư mục logs nếu nó không tồn tại
echo Dang kiem tra thu muc logs...
if not exist "logs" (
    echo Dang tao thu muc logs...
    mkdir logs
    echo Da tao thanh cong thu muc logs!
) else (
    echo Thu muc logs da ton tai!
)
echo.

REM Chuyển trực tiếp đến phần chạy từ config mà không hiển thị menu
goto :run_from_config

:main_menu
cls
echo ===================================
echo MENU CHINH:
echo ===================================
echo 1. Thiet lap moi truong (setup)
echo 2. Chay truc tiep voi thong tin tu command line
echo 3. Chay voi cau hinh tu file config.txt
echo 4. Chinh sua file config.txt
echo 5. Thoat
echo.

set /p option="Nhap lua chon cua ban (1-5): "

if "%option%"=="1" goto :setup
if "%option%"=="2" goto :run_direct
if "%option%"=="3" goto :run_from_config
if "%option%"=="4" goto :edit_config
if "%option%"=="5" exit
echo Lua chon khong hop le, vui long thu lai!
timeout /t 2 >nul
goto :main_menu

:run_direct
cls
echo ===================================
echo CHAY UNG DUNG - NHAP TRUC TIEP
echo ===================================
echo.
echo LUU Y QUAN TRONG:
echo 1. Dia chi URL phai dang metruyencv.info (khong phai .com hoac .biz)
echo 2. Ban se can nhap:
echo    - Email/tai khoan metruyencv
echo    - Mat khau
echo    - O dia luu truyen (C/D)
echo    - So ket noi toi da (50 la gia tri toi uu)
echo.

echo BAM PHIM BAT KY DE TIEP TUC...
pause >nul
echo.
echo =================================== 
echo DANG KHOI DONG UNG DUNG...
echo =================================== 
echo.

echo Chi tiet quy trinh tai se duoc ghi vao thu muc logs
echo.
python main.py

echo.
echo Da hoan thanh chay ung dung.
echo Chi tiet quy trinh co the duoc xem trong thu muc logs
pause
goto :main_menu

:run_from_config
cls
echo ===================================
echo CHAY TU FILE CONFIG
echo ===================================
echo.

REM Kiểm tra file config.txt có tồn tại không
if not exist "config.txt" (
    echo [LOI] Khong tim thay file config.txt
    echo Vui long chon tuy chon 1 de thiet lap hoac tuy chon 4 de tao file config.
    pause
    goto :main_menu
)

echo [OK] Da tim thay file cau hinh config.txt
echo Dang doc thong tin cau hinh...
echo.

REM Đọc các giá trị từ file config.txt
for /f "tokens=1,2 delims==" %%a in ('type config.txt ^| findstr /v "#" ^| findstr /r "."') do (
    set "%%a=%%b"
)

REM Kiểm tra và điều chỉnh URL từ metruyencv.info sang metruyencv.com
echo %novel_url% | findstr /C:"metruyencv.info" > nul
if not errorlevel 1 (
    echo [CANH BAO] Phat hien URL metruyencv.info. Dang chuyen sang metruyencv.com...
    set "novel_url=!novel_url:metruyencv.info=metruyencv.com!"
    echo URL moi: %novel_url%
    
    REM Cập nhật URL trong file config.txt
    powershell -Command "(Get-Content config.txt) -replace 'metruyencv\.info', 'metruyencv.com' | Set-Content config.txt"
    echo Da cap nhat URL trong file config.txt.
    echo.
)

echo Thong tin cau hinh:
echo - Email: %email%
echo - Mat khau: ****** (an)
echo - O dia luu tru: %disk%
echo - So ket noi toi da: %max_connections%
echo - URL truyen: %novel_url%
echo - Chuong bat dau: %start_chapter%
echo - Chuong ket thuc: %end_chapter%
echo.

echo Ban co muon tiep tuc voi cau hinh nay? (Y/N)
set /p choice="Lua chon cua ban: "
if /i not "%choice%"=="Y" (
    goto :main_menu
)

echo.
echo Dang chay chuong trinh...
echo Chi tiet quy trinh tai se duoc ghi vao thu muc logs
echo.

REM DEBUG: Hiển thị giá trị biến trước khi thiết lập
echo DEBUG - Truoc khi thiet lap:
echo Novel URL: %novel_url%
echo Start Chapter: %start_chapter%
echo End Chapter: %end_chapter%
echo.

REM Thiết lập biến môi trường thay vì sử dụng input.txt
set "NOVEL_URL=%novel_url%"
set "START_CHAPTER=%start_chapter%"
set "END_CHAPTER=%end_chapter%"
REM Đánh dấu là chạy tự động để không hiện prompt
set "AUTOMATED_RUN=1"

REM DEBUG: Hiển thị giá trị biến sau khi thiết lập
echo DEBUG - Sau khi thiet lap:
echo Novel URL (env): %NOVEL_URL%
echo Start Chapter (env): %START_CHAPTER%
echo End Chapter (env): %END_CHAPTER%
echo Automated Run: %AUTOMATED_RUN%
echo.

REM Truyền biến vào qua tham số dòng lệnh thay vì biến môi trường
python main.py "%novel_url%" "%start_chapter%" "%end_chapter%"

echo.
echo Chuong trinh da ket thuc. Vui long kiem tra file EPUB trong thu muc %disk%:/novel/
echo Chi tiet qua trinh tai co the xem trong thu muc logs
echo.
pause
goto :main_menu

:edit_config
cls
echo ===================================
echo CHINH SUA FILE CAU HINH
echo ===================================
echo.

REM Kiểm tra file config.txt có tồn tại không, nếu không thì tạo mới
if not exist "config.txt" (
    echo File config.txt khong ton tai. Dang tao file mau...
    echo # Cau hinh tai khoan > config.txt
    echo email=your_email@example.com >> config.txt
    echo password=your_password >> config.txt
    echo. >> config.txt
    echo # Cai dat luu tru va hieu suat >> config.txt
    echo disk=D >> config.txt
    echo max_connections=50 >> config.txt
    echo. >> config.txt
    echo # URL truyen (luu y phai dung dang metruyencv.info) >> config.txt
    echo novel_url=https://metruyencv.info/truyen/your-novel-url >> config.txt
    echo. >> config.txt
    echo # Chon chuong can tai >> config.txt
    echo start_chapter=1 >> config.txt
    echo end_chapter=100 >> config.txt
    echo Da tao file config.txt mau. Vui long chinh sua thong tin.
)

echo Mo file config.txt trong notepad...
notepad config.txt
goto :main_menu

:setup
cls
echo ===================================
echo THIET LAP MOI TRUONG MTC_DOWNLOAD
echo ===================================
echo.

REM Kiem tra Python da duoc cai dat chua
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Python chua duoc cai dat. Vui long cai dat Python tu https://www.python.org/downloads/
    echo Dam bao danh dau vao "Add Python to PATH" trong qua trinh cai dat.
    pause
    goto :main_menu
)

echo [OK] Da phat hien Python.
echo.

echo ===================================
echo TAO THU MUC LOGS
echo ===================================
echo.

if not exist "logs" (
    echo Dang tao thu muc logs...
    mkdir logs
    echo [OK] Da tao thu muc logs thanh cong.
) else (
    echo [OK] Thu muc logs da ton tai.
)
echo.

echo ===================================
echo CAI DAT CAC GOI PYTHON CAN THIET
echo ===================================
echo.

echo Dang cai dat cac goi Python...
pip install -U pip
pip install httpx beautifulsoup4 ebooklib async-lru backoff playwright pytesseract Pillow appdirs tqdm lxml

echo [OK] Da cai dat cac goi Python thanh cong.
echo.

echo ===================================
echo CAI DAT TRINH DUYET CHO PLAYWRIGHT
echo ===================================
echo.

echo Dang cai dat trinh duyet Firefox cho Playwright...
python -m playwright install firefox

echo [OK] Da cai dat thanh cong trinh duyet cho Playwright.
echo.

echo ===================================
echo SUA CHU HE THONG MAC DINH
echo ===================================
echo.

echo Dang kiem tra font chu trong thu muc Windows...
if not exist "C:\Windows\Fonts\times.ttf" (
    echo [CANH BAO] Khong tim thay font Times New Roman trong he thong.
    echo Vui long cai dat font nay de co trai nghiem tot nhat.
) else (
    echo [OK] Da tim thay font Times New Roman trong he thong.
)
echo.

echo ===================================
echo KIEM TRA TESSERACT OCR
echo ===================================
echo.

if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo [CANH BAO] Khong tim thay Tesseract OCR trong he thong.
    echo De su dung chuc nang OCR, ban can cai dat Tesseract OCR tu:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Thiet lap se tiep tuc ma khong co chuc nang OCR.
) else (
    echo [OK] Da tim thay Tesseract OCR trong he thong.
)
echo.

echo ===================================
echo THIET LAP HOAN TAT
echo ===================================
echo.
echo Moi truong da duoc thiet lap thanh cong.
echo Bay gio ban co the chay ung dung bang cach chon tuy chon 3 trong menu chinh.
echo.
echo BAM PHIM BAT KY DE TRO VE MENU CHINH...
pause >nul
goto :main_menu
