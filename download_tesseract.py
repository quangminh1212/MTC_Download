#!/usr/bin/env python3
"""
Script để tải và cài đặt Tesseract-OCR tự động
"""

import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

def download_file(url, filename):
    """Tải file từ URL"""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Giải nén file zip"""
    print(f"Extracting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✅ Extracted to {extract_to}")
        return True
    except Exception as e:
        print(f"❌ Error extracting {zip_path}: {e}")
        return False

def setup_tesseract():
    """Cài đặt Tesseract-OCR"""
    print("=" * 50)
    print("🔧 TESSERACT-OCR AUTO INSTALLER")
    print("=" * 50)
    print()
    
    # Kiểm tra xem đã có Tesseract chưa
    tesseract_path = Path("Tesseract-OCR/tesseract.exe")
    if tesseract_path.exists():
        print("✅ Tesseract-OCR already installed!")
        print(f"   Location: {tesseract_path.absolute()}")
        return True
    
    print("📥 Tesseract-OCR not found. Starting download...")
    print()
    
    # URL cho Tesseract Windows (portable version)
    # Sử dụng phiên bản portable để dễ dàng copy
    tesseract_url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    
    print("⚠️  MANUAL INSTALLATION REQUIRED")
    print("=" * 50)
    print()
    print("Due to the complexity of Tesseract installation, please follow these steps:")
    print()
    print("1. Download Tesseract from:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("2. Install it to any location (e.g., C:\\Program Files\\Tesseract-OCR)")
    print()
    print("3. Copy the entire installation folder to this project directory")
    print("   and rename it to 'Tesseract-OCR'")
    print()
    print("4. The final structure should be:")
    print(f"   {os.getcwd()}\\Tesseract-OCR\\tesseract.exe")
    print()
    print("5. Make sure the following files exist:")
    print("   - Tesseract-OCR\\tesseract.exe")
    print("   - Tesseract-OCR\\tessdata\\vie.traineddata (for Vietnamese)")
    print("   - Tesseract-OCR\\tessdata\\eng.traineddata (for English)")
    print()
    
    # Mở trang download
    try:
        import webbrowser
        print("🌐 Opening download page in browser...")
        webbrowser.open("https://github.com/UB-Mannheim/tesseract/wiki")
    except:
        pass
    
    return False

def verify_tesseract():
    """Kiểm tra Tesseract có hoạt động không"""
    tesseract_path = Path("Tesseract-OCR/tesseract.exe")
    
    if not tesseract_path.exists():
        print("❌ tesseract.exe not found")
        return False
    
    # Kiểm tra tessdata
    tessdata_path = Path("Tesseract-OCR/tessdata")
    if not tessdata_path.exists():
        print("❌ tessdata folder not found")
        return False
    
    # Kiểm tra language files
    eng_data = tessdata_path / "eng.traineddata"
    vie_data = tessdata_path / "vie.traineddata"
    
    if not eng_data.exists():
        print("⚠️  English language data not found (eng.traineddata)")
    else:
        print("✅ English language data found")
    
    if not vie_data.exists():
        print("⚠️  Vietnamese language data not found (vie.traineddata)")
        print("   You may need to download it separately for Vietnamese OCR")
    else:
        print("✅ Vietnamese language data found")
    
    print(f"✅ Tesseract-OCR installation verified at: {tesseract_path.absolute()}")
    return True

def main():
    """Hàm chính"""
    try:
        if not setup_tesseract():
            print()
            print("=" * 50)
            print("⏳ WAITING FOR MANUAL INSTALLATION")
            print("=" * 50)
            print()
            print("After you complete the manual installation, press Enter to verify...")
            input()
            
            if verify_tesseract():
                print()
                print("🎉 Tesseract-OCR installation completed successfully!")
            else:
                print()
                print("❌ Tesseract-OCR installation verification failed.")
                print("Please check the installation and try again.")
        else:
            verify_tesseract()
            
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
