#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra đăng nhập với XPath đã cập nhật
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

def test_login_final():
    """Test đăng nhập với XPath chính xác"""
    print("=== Test Login Final ===")
    
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
        
        # Tìm nút menu
        print("Đang tìm nút menu...")
        menu_button = None
        try:
            menu_button = driver.find_element(By.XPATH, "//button[@data-x-bind=\"OpenModal('menu')\"]")
            if menu_button.is_displayed() and menu_button.is_enabled():
                print("✓ Tìm thấy nút menu")
            else:
                menu_button = None
        except:
            pass
        
        if menu_button:
            # Click vào nút menu
            print("Đang click nút menu...")
            try:
                driver.execute_script("arguments[0].click();", menu_button)
                time.sleep(2)
                print("✓ Đã click nút menu")
            except Exception as e:
                print(f"❌ Lỗi khi click nút menu: {e}")
                driver.quit()
                return
        
        # Tìm nút đăng nhập
        print("Đang tìm nút đăng nhập...")
        login_button = None
        try:
            login_button = driver.find_element(By.XPATH, "//button[@data-x-bind=\"OpenModal('login')\"]")
            if login_button.is_displayed() and login_button.is_enabled():
                print("✓ Tìm thấy nút đăng nhập")
            else:
                login_button = None
        except:
            pass
        
        if not login_button:
            print("❌ Không tìm thấy nút đăng nhập")
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
        
        # Tìm trường email
        print("Đang tìm trường email...")
        email_field = None
        email_xpaths = [
            "//input[@data-x-model='form.email']",
            "//input[@placeholder='email']"
        ]
        
        for xpath in email_xpaths:
            try:
                field = driver.find_element(By.XPATH, xpath)
                if field.is_displayed() and field.is_enabled():
                    email_field = field
                    print(f"✓ Tìm thấy trường email: {xpath}")
                    break
            except:
                continue
        
        if not email_field:
            print("❌ Không tìm thấy trường email")
            driver.quit()
            return
        
        # Tìm trường password
        print("Đang tìm trường password...")
        password_field = None
        password_xpaths = [
            "//input[@data-x-model='form.password']",
            "//input[@placeholder='password']",
            "//input[@type='password']"
        ]
        
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
            email_field.clear()
            email_field.send_keys(username)
            print("✓ Đã điền email")
            
            password_field.clear()
            password_field.send_keys(password)
            print("✓ Đã điền password")
        except Exception as e:
            print(f"❌ Lỗi khi điền thông tin: {e}")
            driver.quit()
            return
        
        # Tìm nút submit
        print("Đang tìm nút submit...")
        submit_button = None
        submit_xpaths = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Đăng nhập')]",
            "//button[contains(text(), 'Login')]",
            "//input[@value='Đăng nhập']",
            "//input[@value='Login']"
        ]
        
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
                time.sleep(5)
                print("✓ Đã click nút submit")
            except Exception as e:
                print(f"❌ Lỗi khi click submit: {e}")
        else:
            print("⚠️  Không tìm thấy nút submit, thử Enter")
            try:
                password_field.send_keys("\n")
                time.sleep(5)
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
            print("⚠️  Không thể xác nhận đăng nhập thành công, nhưng có thể đã đăng nhập")
        
        # Lưu HTML sau khi đăng nhập
        html_after = driver.page_source
        with open('login_success.html', 'w', encoding='utf-8') as f:
            f.write(html_after)
        print("✓ Đã lưu HTML sau đăng nhập vào login_success.html")
        
        driver.quit()
        print("✓ Test hoàn thành")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_final()
