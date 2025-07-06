@echo off 
chcp 65001 >nul 
 
echo =================================== 
echo MTC DOWNLOADER - CHAY UNG DUNG 
echo =================================== 
echo. 
echo LUU Y QUAN TRONG: 
echo 1. Can su dung Command Prompt, khong phai PowerShell 
echo 2. Dia chi URL phai dang metruyencv.info (khong phai .com hoac .biz) 
echo 3. Neu lan dau tien chay, ban se can nhap: 
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
 
cmd /k python main.py 
