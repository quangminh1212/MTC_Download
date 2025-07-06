import os
import sys
import subprocess
import urllib.request
import shutil
import time
import tempfile

def print_header(message):
    print("\n" + "="*50)
    print(f"    {message}")
    print("="*50 + "\n")

def download_with_powershell(url, output_file):
    print(f'Downloading {output_file} using PowerShell...')
    try:
        ps_command = f'[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri "{url}" -OutFile "{output_file}" -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"'
        process = subprocess.run(["powershell", "-Command", ps_command], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             shell=True)
        
        if process.returncode == 0 and os.path.exists(output_file):
            print(f'Download successful!')
            return True
        else:
            print(f'PowerShell download failed: {process.stderr.decode("utf-8", errors="ignore")}')
            return False
    except Exception as e:
        print(f'PowerShell download error: {e}')
        return False

def setup_minimal_tesseract():
    """Create minimal Tesseract structure with Vietnamese language data"""
    print_header("SETTING UP MINIMAL TESSERACT")
    
    tesseract_dir = 'Tesseract-OCR'
    os.makedirs(tesseract_dir, exist_ok=True)
    
    # Create dummy tesseract.exe file
    with open(os.path.join(tesseract_dir, 'tesseract.exe'), 'w') as f:
        f.write('# Dummy file created during setup. Please install Tesseract OCR properly.')
    
    # Create tessdata directory
    tessdata_dir = os.path.join(tesseract_dir, 'tessdata')
    os.makedirs(tessdata_dir, exist_ok=True)
    
    # Download Vietnamese language data
    vie_url = "https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata"
    vie_path = os.path.join(tessdata_dir, "vie.traineddata")
    
    success = download_with_powershell(vie_url, vie_path)
    
    if os.path.exists(vie_path):
        print("✅ Vietnamese language data downloaded successfully")
        return True
    else:
        print("⚠️ Failed to download Vietnamese language data")
        # Create empty file to prevent errors
        with open(vie_path, 'w') as f:
            f.write('# Placeholder file. Please download vie.traineddata manually.')
        return False

def show_manual_instructions():
    print("\nTo manually install Tesseract OCR:")
    print("1. Download from: https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-5.3.3.20231005.exe")
    print("2. Install to: C:\\VF\\MTC_Download\\Tesseract-OCR")
    print("3. Make sure to select Vietnamese language data during installation")
    print("\nAlternatively, download Vietnamese language data file manually:")
    print("1. Download from: https://github.com/tesseract-ocr/tessdata/raw/main/vie.traineddata")
    print("2. Save to: C:\\VF\\MTC_Download\\Tesseract-OCR\\tessdata\\vie.traineddata")

if __name__ == "__main__":
    print_header("TESSERACT OCR SETUP")
    tesseract_dir = 'Tesseract-OCR'
    
    if os.path.exists(os.path.join(tesseract_dir, 'tesseract.exe')) and os.path.getsize(os.path.join(tesseract_dir, 'tesseract.exe')) > 100:
        print(f'✅ Tesseract is already installed at {tesseract_dir}')
    else:
        success = setup_minimal_tesseract()
        if success:
            print("✅ Minimal Tesseract setup complete")
        else:
            print("⚠️ Minimal Tesseract setup partially completed")
        
        show_manual_instructions()
            
    print("\nPress Enter to continue with the setup...")
    input() 