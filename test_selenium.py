#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Selenium với trình duyệt mặc định
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

def create_driver():
    """Tạo WebDriver với trình duyệt mặc định, không headless"""
    print("Đang khởi tạo trình duyệt...")
    
    # Thử Chrome trước
    try:
        chrome_options = Options()
        # Không sử dụng headless - để hiển thị trình duyệt
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✓ Đã khởi tạo Chrome browser")
        return driver
    except Exception as e:
        print(f"Chrome không khả dụng: {e}")
    
    # Thử Firefox
    try:
        firefox_options = FirefoxOptions()
        # Không sử dụng headless
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference('useAutomationExtension', False)
        
        driver = webdriver.Firefox(options=firefox_options)
        print("✓ Đã khởi tạo Firefox browser")
        return driver
    except Exception as e:
        print(f"Firefox không khả dụng: {e}")
    
    # Thử Edge
    try:
        edge_options = EdgeOptions()
        # Không sử dụng headless
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Edge(options=edge_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✓ Đã khởi tạo Edge browser")
        return driver
    except Exception as e:
        print(f"Edge không khả dụng: {e}")
    
    raise Exception("Không thể khởi tạo bất kỳ trình duyệt nào! Vui lòng cài đặt Chrome, Firefox hoặc Edge.")

def test_metruyencv():
    """Test truy cập MeTruyenCV"""
    driver = None
    try:
        driver = create_driver()
        
        # Test URL
        test_url = "https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong"
        print(f"\nĐang test URL: {test_url}")
        
        driver.get(test_url)
        time.sleep(3)
        
        # Lấy title
        title = driver.title
        print(f"Title: {title}")
        
        # Tìm tên truyện
        try:
            story_title = driver.find_element(By.TAG_NAME, "h1").text
            print(f"Tên truyện: {story_title}")
        except:
            print("Không tìm thấy tên truyện")
        
        # Tìm nút đọc truyện
        try:
            read_buttons = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'chuong-1')] | //a[contains(@href, 'chuong-1')]")
            if read_buttons:
                button = read_buttons[0]
                if button.tag_name == 'button':
                    onclick = button.get_attribute('onclick')
                    print(f"Nút đọc onclick: {onclick}")
                else:
                    href = button.get_attribute('href')
                    print(f"Link đọc href: {href}")
            else:
                print("Không tìm thấy nút/link đọc truyện")
        except Exception as e:
            print(f"Lỗi khi tìm nút đọc: {e}")
        
        # Test chương đầu tiên
        chapter_url = "https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong/chuong-1"
        print(f"\nĐang test chương: {chapter_url}")
        
        driver.get(chapter_url)
        time.sleep(3)
        
        # Tìm script chứa chapterData
        scripts = driver.find_elements(By.TAG_NAME, "script")
        found_chapter_data = False
        
        for script in scripts:
            try:
                script_content = driver.execute_script("return arguments[0].innerHTML;", script)
                if script_content and 'chapterData' in script_content:
                    print("✓ Tìm thấy chapterData trong script!")
                    found_chapter_data = True
                    
                    # Hiển thị một phần script
                    preview = script_content[:200] + "..." if len(script_content) > 200 else script_content
                    print(f"Script preview: {preview}")
                    break
            except:
                continue
        
        if not found_chapter_data:
            print("✗ Không tìm thấy chapterData")
        
        print("\n✓ Test hoàn thành! Trình duyệt sẽ đóng sau 5 giây...")
        time.sleep(5)
        
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("=== Test Selenium với MeTruyenCV ===")
    test_metruyencv()
