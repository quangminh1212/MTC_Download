#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test XPath selectors cho MeTruyenCV
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_selectors():
    """Test các XPath selector"""
    
    # Thiết lập Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # URL test
        test_url = "https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong"
        print(f"Đang test URL: {test_url}")
        
        driver.get(test_url)
        time.sleep(3)
        
        print("\n=== TEST XPATH SELECTORS ===")
        
        # Test tên truyện
        title_selectors = [
            "//h1[contains(@class, 'title')]",
            "//h1[contains(@class, 'story-title')]", 
            "//h1[@class='title']",
            "//h1"
        ]
        
        print("\n1. Test tên truyện:")
        for i, selector in enumerate(title_selectors, 1):
            try:
                element = driver.find_element(By.XPATH, selector)
                print(f"   ✅ Selector {i}: {selector}")
                print(f"      Text: {element.text[:50]}...")
                break
            except:
                print(f"   ❌ Selector {i}: {selector}")
        
        # Test tác giả
        author_selectors = [
            "//a[contains(@href, '/tac-gia/')]",
            "//span[contains(@class, 'author')]"
        ]
        
        print("\n2. Test tác giả:")
        for i, selector in enumerate(author_selectors, 1):
            try:
                element = driver.find_element(By.XPATH, selector)
                print(f"   ✅ Selector {i}: {selector}")
                print(f"      Text: {element.text}")
                break
            except:
                print(f"   ❌ Selector {i}: {selector}")
        
        # Test danh sách chương
        chapter_selectors = [
            "//a[contains(@href, '/chuong-')]",
            "//a[contains(@href, 'chuong')]"
        ]
        
        print("\n3. Test danh sách chương:")
        for i, selector in enumerate(chapter_selectors, 1):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"   ✅ Selector {i}: {selector}")
                    print(f"      Tìm thấy {len(elements)} chương")
                    if len(elements) > 0:
                        print(f"      Chương đầu: {elements[0].text[:30]}...")
                        print(f"      URL: {elements[0].get_attribute('href')}")
                    break
                else:
                    print(f"   ❌ Selector {i}: {selector} (không tìm thấy element)")
            except Exception as e:
                print(f"   ❌ Selector {i}: {selector} (lỗi: {e})")
        
        # Test nút mục lục
        muc_luc_selectors = [
            "//a[contains(text(), 'Mục Lục')]",
            "//a[contains(text(), 'Danh sách chương')]",
            "//button[contains(text(), 'Mục Lục')]"
        ]
        
        print("\n4. Test nút mục lục:")
        for i, selector in enumerate(muc_luc_selectors, 1):
            try:
                element = driver.find_element(By.XPATH, selector)
                print(f"   ✅ Selector {i}: {selector}")
                print(f"      Text: {element.text}")
                break
            except:
                print(f"   ❌ Selector {i}: {selector}")
        
        # Test trang chương (lấy URL chương đầu tiên nếu có)
        try:
            chapter_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/chuong-')]")
            if chapter_elements:
                first_chapter_url = chapter_elements[0].get_attribute('href')
                print(f"\n5. Test trang chương: {first_chapter_url}")
                
                driver.get(first_chapter_url)
                time.sleep(2)
                
                content_selectors = [
                    "//div[@id='chapter-content']",
                    "//div[contains(@class, 'chapter-content')]",
                    "//div[contains(@class, 'content')]",
                    "//div[contains(@class, 'story-content')]",
                    "//div[@class='content']"
                ]
                
                for i, selector in enumerate(content_selectors, 1):
                    try:
                        element = driver.find_element(By.XPATH, selector)
                        content = element.text.strip()
                        if content:
                            print(f"   ✅ Selector {i}: {selector}")
                            print(f"      Nội dung: {content[:100]}...")
                            break
                    except:
                        print(f"   ❌ Selector {i}: {selector}")
        except Exception as e:
            print(f"\n5. Không thể test trang chương: {e}")
        
        print("\n=== KẾT THÚC TEST ===")
        
    except Exception as e:
        print(f"Lỗi khi test: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_selectors()
