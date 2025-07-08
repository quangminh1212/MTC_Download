#!/usr/bin/env python3
"""
Script kiểm tra dependencies cho MeTruyenCV Downloader
"""

import sys
import os
import subprocess

def check_python_version():
    """Kiểm tra phiên bản Python"""
    print("🔍 Kiểm tra phiên bản Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Cần Python 3.8+")
        return False

def check_module(module_name, import_name=None):
    """Kiểm tra module Python"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print(f"✅ {module_name} - OK")
        return True
    except ImportError:
        print(f"❌ {module_name} - Chưa cài đặt")
        return False

def check_tesseract():
    """Kiểm tra Tesseract-OCR"""
    print("🔍 Kiểm tra Tesseract-OCR...")
    tesseract_path = os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe")
    
    if os.path.exists(tesseract_path):
        print(f"✅ Tesseract-OCR tìm thấy tại: {tesseract_path}")
        return True
    else:
        print(f"❌ Tesseract-OCR không tìm thấy tại: {tesseract_path}")
        print("   Vui lòng tải và cài đặt từ: https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def check_playwright_browsers():
    """Kiểm tra Playwright browsers"""
    print("🔍 Kiểm tra Playwright browsers...")
    try:
        result = subprocess.run(["playwright", "install", "--dry-run"], 
                              capture_output=True, text=True, timeout=10)
        if "firefox" in result.stdout.lower():
            print("✅ Playwright browsers - OK")
            return True
        else:
            print("❌ Playwright browsers - Chưa cài đặt")
            print("   Chạy: playwright install firefox")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Playwright - Chưa cài đặt hoặc không thể kiểm tra")
        return False

def main():
    """Hàm chính"""
    print("=" * 50)
    print("🔧 KIỂM TRA DEPENDENCIES - MeTruyenCV Downloader")
    print("=" * 50)
    print()
    
    all_ok = True
    
    # Kiểm tra Python
    if not check_python_version():
        all_ok = False
    print()
    
    # Kiểm tra các module Python
    print("🔍 Kiểm tra Python packages...")
    modules = [
        ("httpx", "httpx"),
        ("beautifulsoup4", "bs4"),
        ("ebooklib", "ebooklib"),
        ("tqdm", "tqdm"),
        ("backoff", "backoff"),
        ("playwright", "playwright"),
        ("pytesseract", "pytesseract"),
        ("Pillow", "PIL"),
        ("appdirs", "appdirs"),
        ("async-lru", "async_lru"),
        ("lxml", "lxml")
    ]
    
    for module_name, import_name in modules:
        if not check_module(module_name, import_name):
            all_ok = False
    print()
    
    # Kiểm tra Tesseract
    if not check_tesseract():
        all_ok = False
    print()
    
    # Kiểm tra Playwright browsers
    if not check_playwright_browsers():
        all_ok = False
    print()
    
    # Kết quả
    print("=" * 50)
    if all_ok:
        print("🎉 TẤT CẢ DEPENDENCIES ĐÃ SẴN SÀNG!")
        print("Bạn có thể chạy ứng dụng bằng: python main.py hoặc python fast.py")
    else:
        print("⚠️  CÓ MỘT SỐ VẤN ĐỀ CẦN KHẮC PHỤC")
        print("Vui lòng cài đặt các dependencies bị thiếu và chạy lại script này.")
        print("Hoặc chạy setup.bat để tự động cài đặt.")
    print("=" * 50)
    
    return all_ok

if __name__ == "__main__":
    try:
        success = main()
        input("\nNhấn Enter để thoát...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Đã hủy bởi người dùng")
        sys.exit(1)
