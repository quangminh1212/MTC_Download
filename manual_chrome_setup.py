#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thiết lập ChromeDriver thủ công
"""

import os
import requests
import zipfile
import subprocess
import sys
import json
from pathlib import Path

def get_chrome_version():
    """Lấy phiên bản Chrome đã cài đặt"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            try:
                # Lấy version từ file properties
                result = subprocess.run([
                    'powershell', 
                    f'(Get-ItemProperty "{chrome_path}").VersionInfo.ProductVersion'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"Phiên bản Chrome: {version}")
                    return version.split('.')[0]  # Chỉ lấy major version
            except:
                pass
    
    print("Không tìm thấy Chrome hoặc không thể lấy version")
    return None

def download_chromedriver(version):
    """Tải ChromeDriver thủ công"""
    try:
        # URL trực tiếp tải ChromeDriver
        base_url = "https://storage.googleapis.com/chrome-for-testing-public"

        # Thử các version gần nhất
        versions_to_try = [
            f"{version}.0.0.0",
            f"{version}.0.0.1",
            f"{version}.0.0.2",
            "131.0.6778.85",  # Version stable
            "130.0.6723.116",
            "129.0.6668.100"
        ]

        print("Đang thử tải ChromeDriver...")

        for ver in versions_to_try:
            try:
                chromedriver_url = f"{base_url}/{ver}/win64/chromedriver-win64.zip"
                print(f"Thử version {ver}...")

                response = requests.get(chromedriver_url, timeout=30)
                if response.status_code == 200:
                    print(f"✓ Tìm thấy ChromeDriver version {ver}")
                    break
            except:
                continue
        else:
            print("Không tìm thấy ChromeDriver phù hợp")
            return None

        print(f"Đang tải ChromeDriver từ: {chromedriver_url}")

        # Tải file
        response = requests.get(chromedriver_url, timeout=60)
        zip_path = "chromedriver.zip"
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Giải nén
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("chromedriver_temp")
        
        # Tìm file chromedriver.exe
        chromedriver_exe = None
        for root, _, files in os.walk("chromedriver_temp"):
            for file in files:
                if file == "chromedriver.exe":
                    chromedriver_exe = os.path.join(root, file)
                    break
        
        if chromedriver_exe:
            # Copy vào thư mục hiện tại
            import shutil
            shutil.copy2(chromedriver_exe, "chromedriver.exe")
            
            # Dọn dẹp
            shutil.rmtree("chromedriver_temp")
            os.remove(zip_path)
            
            print("✓ Đã tải ChromeDriver thành công!")
            return os.path.abspath("chromedriver.exe")
        
        return None
        
    except Exception as e:
        print(f"Lỗi khi tải ChromeDriver: {e}")
        return None

def main():
    print("=== THIẾT LẬP CHROMEDRIVER THỦ CÔNG ===")
    
    # Lấy version Chrome
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("Vui lòng cài đặt Google Chrome trước!")
        return
    
    # Tải ChromeDriver
    chromedriver_path = download_chromedriver(chrome_version)
    
    if chromedriver_path:
        print(f"ChromeDriver đã được lưu tại: {chromedriver_path}")
        print("\nBây giờ bạn có thể chạy: python simple_downloader.py")
    else:
        print("Không thể tải ChromeDriver!")

if __name__ == "__main__":
    main()
