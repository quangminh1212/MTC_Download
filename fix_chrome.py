#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sửa lỗi ChromeDriver
"""

import os
import shutil
import subprocess
import sys

def clear_webdriver_cache():
    """Xóa cache webdriver-manager"""
    cache_dirs = [
        os.path.expanduser("~/.wdm"),
        os.path.expanduser("~/AppData/Local/.wdm"),
        os.path.expanduser("~/AppData/Roaming/.wdm")
    ]
    
    print("Đang xóa cache ChromeDriver...")
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✓ Đã xóa: {cache_dir}")
            except:
                print(f"❌ Không thể xóa: {cache_dir}")

def reinstall_packages():
    """Cài đặt lại packages"""
    packages = [
        "selenium",
        "webdriver-manager"
    ]
    
    print("\nĐang cài đặt lại packages...")
    
    for package in packages:
        print(f"Gỡ cài đặt {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package, "-y"], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
        except:
            pass
        
        print(f"Cài đặt lại {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            print(f"✓ Đã cài đặt {package}")
        except:
            print(f"❌ Lỗi khi cài đặt {package}")

def main():
    print("=== SỬA LỖI CHROMEDRIVER ===")
    
    clear_webdriver_cache()
    reinstall_packages()
    
    print("\n=== HOÀN THÀNH ===")
    print("✓ Đã sửa lỗi ChromeDriver!")
    print("Bây giờ thử chạy lại: python simple_downloader.py")

if __name__ == "__main__":
    main()
