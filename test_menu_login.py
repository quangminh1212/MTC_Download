#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để tìm nút menu và nút đăng nhập
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

def test_menu_login():
    """Test tìm nút menu và nút đăng nhập"""
    print("=== Test Menu & Login ===")
    
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
        
        # Truy cập trang chính
        print(f"Đang truy cập: {story_url}")
        driver.get(story_url)
        time.sleep(5)
        
        # Tìm nút menu trước
        print("Đang tìm nút menu...")
        menu_xpaths = [
            "//button[@data-x-bind=\"OpenModal('menu')\"]",
            "//button[contains(@data-x-bind, 'menu')]",
            "//button[contains(@data-x-bind, 'Menu')]",
            "//button[contains(@class, 'menu')]",
            "//div[@class='flex space-x-2']//button",
            "//header//button[last()]",
            "//header//button"
        ]
        
        menu_button = None
        for xpath in menu_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                print(f"Tìm thấy {len(elements)} element với xpath: {xpath}")
                for i, element in enumerate(elements):
                    try:
                        print(f"  Element {i+1}: Tag={element.tag_name}, Text='{element.text}', Class='{element.get_attribute('class')}', Data-x-bind='{element.get_attribute('data-x-bind')}'")
                        if element.is_displayed() and element.is_enabled():
                            menu_button = element
                            print(f"✓ Chọn element này làm menu button")
                            break
                    except Exception as e:
                        print(f"  Lỗi khi kiểm tra element {i+1}: {e}")
                if menu_button:
                    break
            except Exception as e:
                print(f"Lỗi với xpath {xpath}: {e}")
        
        if not menu_button:
            print("❌ Không tìm thấy nút menu")
            driver.quit()
            return
        
        # Click vào nút menu
        print("Đang click nút menu...")
        try:
            driver.execute_script("arguments[0].click();", menu_button)
            time.sleep(3)
            print("✓ Đã click nút menu")
        except Exception as e:
            print(f"❌ Lỗi khi click nút menu: {e}")
            driver.quit()
            return
        
        # Bây giờ tìm nút đăng nhập
        print("Đang tìm nút đăng nhập...")
        login_xpaths = [
            "//button[@data-x-bind=\"OpenModal('login')\"]",
            "//button[contains(@data-x-bind, \"OpenModal('login')\")]",
            "//button[contains(text(), 'Đăng nhập')]",
            "//a[contains(text(), 'Đăng nhập')]",
            "//*[@data-x-bind=\"OpenModal('login')\"]",
            "//*[contains(@data-x-bind, 'login')]"
        ]
        
        login_button = None
        for xpath in login_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                print(f"Tìm thấy {len(elements)} element với xpath: {xpath}")
                for i, element in enumerate(elements):
                    try:
                        print(f"  Element {i+1}: Tag={element.tag_name}, Text='{element.text}', Class='{element.get_attribute('class')}', Data-x-bind='{element.get_attribute('data-x-bind')}'")
                        if element.is_displayed() and element.is_enabled():
                            login_button = element
                            print(f"✓ Chọn element này làm login button")
                            break
                    except Exception as e:
                        print(f"  Lỗi khi kiểm tra element {i+1}: {e}")
                if login_button:
                    break
            except Exception as e:
                print(f"Lỗi với xpath {xpath}: {e}")
        
        if not login_button:
            print("❌ Không tìm thấy nút đăng nhập")
            
            # Lưu HTML sau khi click menu để debug
            html_after_menu = driver.page_source
            with open('after_menu_click.html', 'w', encoding='utf-8') as f:
                f.write(html_after_menu)
            print("✓ Đã lưu HTML sau khi click menu vào after_menu_click.html")
            
            driver.quit()
            return
        
        # Click vào nút đăng nhập
        print("Đang click nút đăng nhập...")
        try:
            driver.execute_script("arguments[0].click();", login_button)
            time.sleep(3)
            print("✓ Đã click nút đăng nhập")
        except Exception as e:
            print(f"❌ Lỗi khi click nút đăng nhập: {e}")
            driver.quit()
            return
        
        # Lưu HTML sau khi click đăng nhập
        html_after_login_click = driver.page_source
        with open('after_login_click.html', 'w', encoding='utf-8') as f:
            f.write(html_after_login_click)
        print("✓ Đã lưu HTML sau khi click đăng nhập vào after_login_click.html")
        
        driver.quit()
        print("✓ Test hoàn thành")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_menu_login()
