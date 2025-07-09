#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test tính năng chọn trình duyệt
"""

import time
from ultra_simple import create_driver

def test_browser_choice():
    """Test các tùy chọn trình duyệt"""
    browsers = ["auto", "edge", "firefox", "chrome", "brave"]
    
    for browser in browsers:
        print(f"\n{'='*50}")
        print(f"Testing browser: {browser}")
        print('='*50)
        
        try:
            driver = create_driver(browser)
            
            # Test đơn giản
            driver.get("https://www.google.com")
            time.sleep(2)
            
            title = driver.title
            print(f"✓ Thành công! Title: {title}")
            
            driver.quit()
            print(f"✓ Đã đóng {browser} browser")
            
        except Exception as e:
            print(f"✗ Lỗi với {browser}: {e}")
        
        print(f"Nghỉ 3 giây trước khi test browser tiếp theo...")
        time.sleep(3)

if __name__ == "__main__":
    print("=== Test Browser Choice ===")
    test_browser_choice()
    print("\n=== Test hoàn thành ===")
