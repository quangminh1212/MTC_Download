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
        # URL API để lấy ChromeDriver
        api_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        
        print("Đang lấy thông tin ChromeDriver...")
        response = requests.get(api_url, timeout=30)
        data = response.json()
        
        # Tìm version phù hợp
        chromedriver_url = None
        for item in data['versions']:
            if item['version'].startswith(version):
                for download in item['downloads'].get('chromedriver', []):
                    if download['platform'] == 'win64':
                        chromedriver_url = download['url']
                        break
                if chromedriver_url:
                    break
        
        if not chromedriver_url:
            print(f"Không tìm thấy ChromeDriver cho Chrome {version}")
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
        for root, dirs, files in os.walk("chromedriver_temp"):
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
