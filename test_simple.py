#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script đơn giản để kiểm tra Selenium và lấy HTML
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

def test_selenium():
    """Test Selenium cơ bản"""
    print("=== Test Selenium ===")
    
    try:
        # Đọc config
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        story_url = config['download']['story_url']
        print(f"URL: {story_url}")
        
        # Tạo Edge driver
        print("Đang khởi tạo Edge...")
        edge_options = EdgeOptions()
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Edge(options=edge_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✓ Đã khởi tạo Edge")
        
        # Truy cập trang
        print(f"Đang truy cập: {story_url}")
        driver.get(story_url)
        time.sleep(5)
        
        # Lấy title
        title = driver.title
        print(f"Title: {title}")
        
        # Lấy HTML
        html = driver.page_source
        print(f"HTML length: {len(html)} characters")
        
        # Lưu HTML để kiểm tra
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✓ Đã lưu HTML vào page_source.html")
        
        # Kiểm tra có chapterData không
        if 'chapterData' in html:
            print("✓ Tìm thấy chapterData trong HTML")
        else:
            print("❌ Không tìm thấy chapterData")
            
        # Kiểm tra có form đăng nhập không
        if 'login' in html.lower() or 'đăng nhập' in html.lower():
            print("✓ Tìm thấy form đăng nhập")
        else:
            print("❌ Không tìm thấy form đăng nhập")
        
        driver.quit()
        print("✓ Test hoàn thành")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_selenium()
