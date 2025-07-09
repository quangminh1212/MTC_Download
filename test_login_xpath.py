#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để tìm nút đăng nhập bằng XPath chính xác
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

def test_login_xpath():
    """Test tìm nút đăng nhập bằng XPath"""
    print("=== Test Login XPath ===")
    
    try:
        # Đọc config
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        story_url = config['download']['story_url']
        username = config['account']['username']
        password = config['account']['password']
        
        print(f"URL: {story_url}")
        print(f"Username: {username}")
        
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
        
        # Tìm nút đăng nhập với các XPath khác nhau
        login_xpaths = [
            "//button[@data-x-bind=\"OpenModal('login')\"]",
            "//button[contains(@data-x-bind, \"OpenModal('login')\")]",
            "//button[contains(text(), 'Đăng nhập')]",
            "//button[text()='Đăng nhập']",
            "//a[contains(text(), 'Đăng nhập')]",
            "//a[text()='Đăng nhập']",
            "//div[contains(text(), 'Đăng nhập')]",
            "//span[contains(text(), 'Đăng nhập')]",
            "//button[@data-x-bind*='login']",
            "//button[@data-x-bind*='Login']",
            "//a[@data-x-bind*='login']",
            "//a[@data-x-bind*='Login']",
            "//button[contains(@onclick, 'login')]",
            "//a[contains(@href, 'login')]",
            "//a[contains(@href, 'dang-nhap')]",
            "//button[contains(@class, 'login')]",
            "//a[contains(@class, 'login')]",
            "//*[@data-x-bind=\"OpenModal('login')\"]",
            "//*[contains(@data-x-bind, 'login')]",
            "//*[contains(@data-x-bind, 'Login')]"
        ]
        
        login_button = None
        found_xpath = None
        
        print("Đang tìm nút đăng nhập...")
        for xpath in login_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        login_button = element
                        found_xpath = xpath
                        print(f"✓ Tìm thấy nút đăng nhập với XPath: {xpath}")
                        print(f"  Text: '{element.text}'")
                        print(f"  Tag: {element.tag_name}")
                        print(f"  Class: {element.get_attribute('class')}")
                        print(f"  Data-x-bind: {element.get_attribute('data-x-bind')}")
                        break
                if login_button:
                    break
            except Exception as e:
                continue
        
        if not login_button:
            print("❌ Không tìm thấy nút đăng nhập")
            
            # Lưu HTML để debug
            html = driver.page_source
            with open('login_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("✓ Đã lưu HTML vào login_debug.html để debug")
            
            # Tìm tất cả các element có chứa "đăng nhập" hoặc "login"
            print("\nTìm tất cả element có chứa 'đăng nhập' hoặc 'login':")
            all_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ĐĂNG NHẬP', 'đăng nhập'), 'đăng nhập') or contains(translate(text(), 'LOGIN', 'login'), 'login')]")
            for i, elem in enumerate(all_elements[:10]):  # Chỉ hiển thị 10 đầu tiên
                try:
                    print(f"  {i+1}. Tag: {elem.tag_name}, Text: '{elem.text}', Class: {elem.get_attribute('class')}")
                except:
                    continue
            
            driver.quit()
            return
        
        # Thử click nút đăng nhập
        print(f"\nĐang click nút đăng nhập...")
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", login_button)
            time.sleep(3)
            print("✓ Đã click nút đăng nhập")
        except Exception as e:
            print(f"❌ Lỗi khi click nút đăng nhập: {e}")
            driver.quit()
            return
        
        # Tìm form đăng nhập
        print("Đang tìm form đăng nhập...")
        
        # Tìm trường username/email
        username_xpaths = [
            "//input[@name='username']",
            "//input[@name='email']", 
            "//input[@type='email']",
            "//input[@placeholder*='email']",
            "//input[@placeholder*='tên']",
            "//input[@placeholder*='Email']",
            "//input[@placeholder*='Username']",
            "//input[@id='username']",
            "//input[@id='email']",
            "//input[contains(@class, 'username')]",
            "//input[contains(@class, 'email')]"
        ]
        
        username_field = None
        for xpath in username_xpaths:
            try:
                field = driver.find_element(By.XPATH, xpath)
                if field.is_displayed() and field.is_enabled():
                    username_field = field
                    print(f"✓ Tìm thấy trường username: {xpath}")
                    break
            except:
                continue
        
        if not username_field:
            print("❌ Không tìm thấy trường username")
            driver.quit()
            return
        
        # Tìm trường password
        password_xpaths = [
            "//input[@name='password']",
            "//input[@type='password']",
            "//input[@id='password']",
            "//input[contains(@class, 'password')]"
        ]
        
        password_field = None
        for xpath in password_xpaths:
            try:
                field = driver.find_element(By.XPATH, xpath)
                if field.is_displayed() and field.is_enabled():
                    password_field = field
                    print(f"✓ Tìm thấy trường password: {xpath}")
                    break
            except:
                continue
        
        if not password_field:
            print("❌ Không tìm thấy trường password")
            driver.quit()
            return
        
        # Điền thông tin đăng nhập
        print("Đang điền thông tin đăng nhập...")
        try:
            username_field.clear()
            username_field.send_keys(username)
            print("✓ Đã điền username")
            
            password_field.clear()
            password_field.send_keys(password)
            print("✓ Đã điền password")
        except Exception as e:
            print(f"❌ Lỗi khi điền thông tin: {e}")
            driver.quit()
            return
        
        # Tìm nút submit
        submit_xpaths = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Đăng nhập')]",
            "//button[contains(text(), 'Login')]",
            "//input[@value='Đăng nhập']",
            "//input[@value='Login']",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'login')]"
        ]
        
        submit_button = None
        for xpath in submit_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        submit_button = element
                        print(f"✓ Tìm thấy nút submit: {xpath}")
                        break
                if submit_button:
                    break
            except:
                continue
        
        if submit_button:
            try:
                driver.execute_script("arguments[0].click();", submit_button)
                time.sleep(3)
                print("✓ Đã click nút submit")
            except Exception as e:
                print(f"❌ Lỗi khi click submit: {e}")
        else:
            print("⚠️  Không tìm thấy nút submit, thử Enter")
            try:
                password_field.send_keys("\n")
                time.sleep(3)
                print("✓ Đã thử submit bằng Enter")
            except Exception as e:
                print(f"❌ Lỗi khi submit bằng Enter: {e}")
        
        # Kiểm tra đăng nhập thành công
        print("Đang kiểm tra đăng nhập...")
        success_indicators = [
            "//a[contains(text(), 'Đăng xuất')]",
            "//a[contains(text(), 'Logout')]", 
            "//a[contains(text(), 'Tài khoản')]",
            "//a[contains(text(), 'Profile')]",
            "//span[contains(@class, 'user')]",
            "//div[contains(@class, 'user')]"
        ]
        
        login_success = False
        for indicator in success_indicators:
            try:
                element = driver.find_element(By.XPATH, indicator)
                if element.is_displayed():
                    print(f"✓ Đăng nhập thành công! Tìm thấy: {indicator}")
                    login_success = True
                    break
            except:
                continue
        
        if not login_success:
            print("⚠️  Không thể xác nhận đăng nhập thành công")
        
        # Lưu HTML sau khi đăng nhập
        html_after = driver.page_source
        with open('after_login.html', 'w', encoding='utf-8') as f:
            f.write(html_after)
        print("✓ Đã lưu HTML sau đăng nhập vào after_login.html")
        
        driver.quit()
        print("✓ Test hoàn thành")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_xpath()
