@echo off
chcp 65001 >nul

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
    exit /b 1
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
echo TAO FILE KHOI CHAY COMMAND PROMPT
echo ===================================
echo.

echo @echo off > run-app.bat
echo chcp 65001 ^>nul >> run-app.bat
echo. >> run-app.bat
echo echo =================================== >> run-app.bat
echo echo MTC DOWNLOADER - CHAY UNG DUNG >> run-app.bat
echo echo =================================== >> run-app.bat
echo echo. >> run-app.bat
echo echo LUU Y QUAN TRONG: >> run-app.bat
echo echo 1. Can su dung Command Prompt, khong phai PowerShell >> run-app.bat
echo echo 2. Dia chi URL phai dang metruyencv.info ^(khong phai .com hoac .biz^) >> run-app.bat
echo echo 3. Neu lan dau tien chay, ban se can nhap: >> run-app.bat
echo echo    - Email/tai khoan metruyencv >> run-app.bat
echo echo    - Mat khau >> run-app.bat
echo echo    - O dia luu truyen ^(C/D^) >> run-app.bat
echo echo    - So ket noi toi da ^(50 la gia tri toi uu^) >> run-app.bat
echo echo. >> run-app.bat
echo echo BAM PHIM BAT KY DE TIEP TUC... >> run-app.bat
echo pause ^>nul >> run-app.bat
echo. >> run-app.bat
echo echo. >> run-app.bat
echo echo =================================== >> run-app.bat
echo echo DANG KHOI DONG UNG DUNG... >> run-app.bat
echo echo =================================== >> run-app.bat
echo echo. >> run-app.bat
echo. >> run-app.bat
echo cmd /k python main.py >> run-app.bat

echo [OK] Da tao file run-app.bat de chay ung dung trong Command Prompt.
echo.

echo ===================================
echo THIET LAP HOAN TAT
echo ===================================
echo.
echo Da hoan tat thiet lap moi truong!
echo.
echo De chay chuong trinh, su dung file run-app.bat de mo trong Command Prompt.
echo Day se giup tranh loi EOFError khi chay trong PowerShell.
echo.
echo THONG TIN BO SUNG:
echo - Duong dan URL phai o dang metruyencv.info (khong phai .com)
echo - File EPUB se duoc luu trong thu muc C:/novel hoac D:/novel (tuy cau hinh)
echo.
pause 
pause 