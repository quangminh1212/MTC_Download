#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra đăng nhập MeTruyenCV
"""

import json
from downloader import create_driver, login_to_site, load_config

def test_login():
    """Test đăng nhập"""
    print("=== Test Đăng Nhập MeTruyenCV ===")
    
    # Đọc config
    config = load_config()
    if not config:
        print("❌ Không đọc được config.json")
        return
    
    account_config = config.get("account", {})
    username = account_config.get("username", "")
    password = account_config.get("password", "")
    
    if not username or not password:
        print("❌ Thiếu username hoặc password trong config.json")
        return
    
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    # Tạo driver
    driver = None
    try:
        print("\n1. Tạo WebDriver...")
        driver = create_driver("auto")
        
        print("\n2. Truy cập trang chủ...")
        driver.get("https://metruyencv.com")
        
        print("\n3. Thử đăng nhập...")
        result = login_to_site(driver, username, password, max_retries=2)
        
        if result:
            print("\n✅ Test đăng nhập THÀNH CÔNG!")
        else:
            print("\n❌ Test đăng nhập THẤT BẠI!")
            
        print("\n4. Kiểm tra URL hiện tại...")
        print(f"Current URL: {driver.current_url}")
        
        print("\n5. Đợi 5 giây để quan sát...")
        import time
        time.sleep(5)
        
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\n6. Đóng trình duyệt...")
            driver.quit()

if __name__ == "__main__":
    test_login()
