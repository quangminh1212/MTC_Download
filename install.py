#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cài đặt dependencies cho MeTruyenCV Downloader
"""

import subprocess
import sys

def install():
    """Cài đặt các package cần thiết"""
    packages = [
        "selenium==4.15.2",
        "webdriver-manager==4.0.1"
    ]
    
    print("Đang cài đặt packages...")
    
    for package in packages:
        print(f"Cài đặt {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Đã cài đặt {package}")
        except:
            print(f"✗ Lỗi khi cài đặt {package}")
    
    print("\nHoàn thành cài đặt!")
    print("Bây giờ bạn có thể chạy: python simple_downloader.py")

if __name__ == "__main__":
    install()
