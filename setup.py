#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script cài đặt cho MeTruyenCV Downloader
"""

import subprocess
import sys
import os

def install_requirements():
    """Cài đặt các package cần thiết"""
    print("Đang cài đặt các package Python...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Cài đặt thành công các package Python!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi cài đặt package: {e}")
        return False
    
    return True

def create_directories():
    """Tạo các thư mục cần thiết"""
    print("Đang tạo thư mục...")
    
    directories = ["truyen", "logs"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Đã tạo thư mục: {directory}")
        else:
            print(f"📁 Thư mục đã tồn tại: {directory}")

def test_installation():
    """Test cài đặt"""
    print("Đang test cài đặt...")
    
    try:
        # Test import các module chính
        import selenium
        from webdriver_manager.chrome import ChromeDriverManager
        import requests
        from bs4 import BeautifulSoup
        
        print("✅ Tất cả module đã được import thành công!")
        
        # Test ChromeDriver
        print("Đang test ChromeDriver...")
        ChromeDriverManager().install()
        print("✅ ChromeDriver hoạt động bình thường!")
        
        return True
    except ImportError as e:
        print(f"❌ Lỗi import module: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi test: {e}")
        return False

def main():
    """Hàm main"""
    print("=" * 50)
    print("    MeTruyenCV Downloader - Setup")
    print("=" * 50)
    
    # Kiểm tra Python version
    if sys.version_info < (3, 7):
        print("❌ Cần Python 3.7 trở lên!")
        return
    
    print(f"✅ Python version: {sys.version}")
    
    # Cài đặt requirements
    if not install_requirements():
        return
    
    # Tạo thư mục
    create_directories()
    
    # Test cài đặt
    if test_installation():
        print("\n" + "=" * 50)
        print("🎉 Cài đặt hoàn tất!")
        print("=" * 50)
        print("\nCách sử dụng:")
        print("1. Chạy script tương tác: python run_downloader.py")
        print("2. Hoặc chỉnh sửa và chạy: python metruyencv_downloader.py")
        print("3. Test selectors: python test_selectors.py")
        print("\nĐọc README.md để biết thêm chi tiết!")
    else:
        print("\n❌ Cài đặt không thành công. Vui lòng kiểm tra lại!")

if __name__ == "__main__":
    main()
