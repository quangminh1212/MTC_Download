#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cài đặt dependencies cho MeTruyenCV Downloader
"""

import subprocess
import sys
import os

def check_chrome():
    """Kiểm tra Google Chrome đã cài đặt chưa"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME'))
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ Tìm thấy Google Chrome tại: {path}")
            return True

    print("❌ Không tìm thấy Google Chrome!")
    print("Vui lòng tải và cài đặt Google Chrome từ: https://www.google.com/chrome/")
    return False

def install():
    """Cài đặt các package cần thiết"""
    print("=== KIỂM TRA HỆ THỐNG ===")

    # Kiểm tra Chrome
    if not check_chrome():
        print("\n⚠️  Cần cài đặt Google Chrome trước khi tiếp tục!")
        return

    print("\n=== CÀI ĐẶT PACKAGES ===")

    packages = [
        "selenium==4.15.2",
        "webdriver-manager==4.0.1"
    ]

    for package in packages:
        print(f"Đang cài đặt {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            print(f"✓ Đã cài đặt {package}")
        except:
            print(f"❌ Lỗi khi cài đặt {package}")
            print("Thử chạy lại với quyền Administrator")

    print("\n=== HOÀN THÀNH ===")
    print("✓ Cài đặt hoàn tất!")
    print("Bây giờ bạn có thể chạy: python simple_downloader.py")
    print("Hoặc sử dụng run.bat")

if __name__ == "__main__":
    install()
