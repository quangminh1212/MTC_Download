#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test đơn giản cho MeTruyenCV Downloader
"""

import time
from downloader import create_driver

def test_browsers():
    """Test các trình duyệt có sẵn"""
    print("=== Test MeTruyenCV Downloader ===")
    
    browsers = ["auto", "edge", "firefox", "chrome", "brave"]
    
    for browser in browsers:
        print(f"\n🔍 Testing {browser}...")
        
        try:
            driver = create_driver(browser)
            
            # Test đơn giản
            driver.get("https://www.google.com")
            time.sleep(1)
            
            title = driver.title
            print(f"✅ {browser}: {title}")
            
            driver.quit()
            
        except Exception as e:
            print(f"❌ {browser}: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_browsers()
