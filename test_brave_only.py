#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Brave Browser riêng
"""

import time
from ultra_simple import create_driver

def test_brave():
    """Test Brave Browser"""
    print("=== Test Brave Browser ===")
    
    try:
        driver = create_driver("brave")
        
        # Test đơn giản
        driver.get("https://www.google.com")
        time.sleep(2)
        
        title = driver.title
        print(f"✓ Thành công! Title: {title}")
        
        driver.quit()
        print("✓ Đã đóng Brave browser")
        
    except Exception as e:
        print(f"✗ Lỗi với Brave: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_brave()
