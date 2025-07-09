#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cài đặt đơn giản cho MeTruyenCV Downloader
"""

import subprocess
import sys
import os

def install_package(package):
    """Cài đặt một package"""
    try:
        print(f"Đang cài đặt {package}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", package, "--upgrade"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✓ Đã cài đặt {package}")
        return True
    except:
        print(f"❌ Lỗi khi cài đặt {package}")
        return False

def main():
    print("=== CÀI ĐẶT PACKAGES ===")
    
    packages = [
        "selenium==4.15.2",
        "webdriver-manager==4.0.1", 
        "requests"
    ]
    
    success = 0
    for package in packages:
        if install_package(package):
            success += 1
    
    print(f"\nĐã cài đặt {success}/{len(packages)} packages")
    
    if success == len(packages):
        print("✓ Cài đặt hoàn tất!")
    else:
        print("⚠️  Một số packages không cài được, nhưng có thể vẫn chạy được")

if __name__ == "__main__":
    main()
