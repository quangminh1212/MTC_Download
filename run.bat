@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION

echo ===================================
echo MTC DOWNLOADER - PHIEN BAN TICH HOP
echo ===================================
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

python main.py

echo.
echo Da hoan thanh chay ung dung.
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

REM DEBUG: Hiển thị giá trị biến sau khi thiết lập
echo DEBUG - Sau khi thiet lap:
echo Novel URL (env): %NOVEL_URL%
echo Start Chapter (env): %START_CHAPTER%
echo End Chapter (env): %END_CHAPTER%
echo.

REM Truyền biến vào qua tham số dòng lệnh thay vì biến môi trường
python main.py "%novel_url%" "%start_chapter%" "%end_chapter%"

echo.
echo Chuong trinh da ket thuc. Vui long kiem tra file EPUB trong thu muc %disk%:/novel/
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

echo [OK] Da cai dat trinh duyet Firefox cho Playwright thanh cong.
echo.

echo ===================================
echo CAP NHAT TESSERACT OCR
echo ===================================
echo.

echo Da phat hien Tesseract OCR tai: C:\Program Files\Tesseract-OCR
echo Dang cap nhat duong dan trong ma nguon...

echo Dang cap nhat duong dan Tesseract OCR trong main.py...
powershell -Command "(Get-Content main.py) -replace 'pytesseract.pytesseract.tesseract_cmd = fr''{file_location}\\Tesseract-OCR\\tesseract.exe''', 'pytesseract.pytesseract.tesseract_cmd = r''C:\\Program Files\\Tesseract-OCR\\tesseract.exe''' | Set-Content main.py"

echo Dang cap nhat duong dan Tesseract OCR trong fast.py...
powershell -Command "(Get-Content fast.py) -replace 'pytesseract.pytesseract.tesseract_cmd = fr''{file_location}\\Tesseract-OCR\\tesseract.exe''', 'pytesseract.pytesseract.tesseract_cmd = r''C:\\Program Files\\Tesseract-OCR\\tesseract.exe''' | Set-Content fast.py"

echo [OK] Da cap nhat duong dan Tesseract OCR thanh cong.
echo.

echo ===================================
echo KIEM TRA GOI NGON NGU TIENG VIET
echo ===================================
echo.

if exist "C:\Program Files\Tesseract-OCR\tessdata\vie.traineddata" (
    echo [OK] Da tim thay goi ngon ngu tieng Viet cho Tesseract OCR.
) else (
    echo [CANH BAO] Khong tim thay goi ngon ngu tieng Viet cho Tesseract OCR.
    echo Ban co muon tai va cai dat goi ngon ngu tieng Viet? (Y/N)
    set /p choice="Lua chon cua ban: "
    if /i "%choice%"=="Y" (
        echo Dang tai goi ngon ngu tieng Viet...
        powershell -Command "$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata' -OutFile 'vie.traineddata'"
        
        if %errorlevel% neq 0 (
            echo [LOI] Khong the tai goi ngon ngu tieng Viet.
            echo Vui long tai thu cong tai: https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata
            echo Va sao chep vao thu muc: C:\Program Files\Tesseract-OCR\tessdata\
        ) else (
            echo Dang cai dat goi ngon ngu tieng Viet...
            echo Thao tac nay co the yeu cau quyen Admin.
            
            REM Thu copy file khong can quyen Admin truoc
            copy /Y "vie.traineddata" "C:\Program Files\Tesseract-OCR\tessdata\" >nul 2>&1
            
            if %errorlevel% neq 0 (
                echo Can quyen Admin de cai dat goi ngon ngu.
                echo Vui long chay lai setup.bat voi quyen Admin hoac sao chep thu cong file vie.traineddata
                echo vao thu muc C:\Program Files\Tesseract-OCR\tessdata\
            ) else (
                echo [OK] Da cai dat goi ngon ngu tieng Viet thanh cong.
                del "vie.traineddata" >nul 2>&1
            )
        )
    ) else (
        echo Ban da bo qua cai dat goi ngon ngu tieng Viet.
        echo Ban can cai dat goi nay de OCR tieng Viet hoat dong chinh xac.
    )
)

echo.

echo ===================================
echo XOA CANH BAO LAYWRIGHT
echo ===================================
echo.

echo Ban co muon xoa canh bao "invalid distribution ~laywright"? (Y/N)
set /p laywright_choice="Lua chon cua ban: "
if /i "%laywright_choice%"=="Y" (
    rmdir /s /q "C:\Users\%USERNAME%\AppData\Roaming\Python\Python312\site-packages\~laywright" 2>nul
    echo Da thu xoa phan phoi ~laywright khong hop le.
)

echo.
echo ===================================
echo XOA CAC FILE DU THUA
echo ===================================
echo.

echo Ban co muon xoa cac file .bat du thua? (Y/N)
echo (run-app.bat, setup.bat, run-from-config.bat)
set /p cleanup_choice="Lua chon cua ban: "
if /i "%cleanup_choice%"=="Y" (
    if exist run-app.bat del run-app.bat
    if exist setup.bat del setup.bat
    if exist run-from-config.bat del run-from-config.bat
    echo Da xoa cac file .bat du thua.
)

echo.
echo Thiet lap hoan tat! Quay lai menu chinh...
timeout /t 3 >nul
goto :main_menu
