#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader - Phiên bản sử dụng Selenium
Sử dụng Selenium với trình duyệt mặc định, không headless
"""

import os
import time
import json
import base64
import re
import gzip
import zlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def create_driver(browser_choice="auto"):
    """Tạo WebDriver với trình duyệt được chọn, không headless"""
    browser_choice = browser_choice.lower()

    if browser_choice == "edge":
        print("Đang khởi tạo Microsoft Edge...")
        return _create_edge_driver()
    elif browser_choice == "firefox":
        print("Đang khởi tạo Mozilla Firefox...")
        return _create_firefox_driver()
    elif browser_choice == "chrome":
        print("Đang khởi tạo Google Chrome...")
        return _create_chrome_driver()
    elif browser_choice == "brave":
        print("Đang khởi tạo Brave Browser...")
        return _create_brave_driver()
    else:
        # Auto mode - thử theo thứ tự ưu tiên
        print("Đang tự động chọn trình duyệt...")

        # Thử Edge trước (trình duyệt mặc định trên Windows)
        try:
            return _create_edge_driver()
        except Exception as e:
            print(f"Edge không khả dụng: {e}")

        # Thử Firefox
        try:
            return _create_firefox_driver()
        except Exception as e:
            print(f"Firefox không khả dụng: {e}")

        # Thử Chrome
        try:
            return _create_chrome_driver()
        except Exception as e:
            print(f"Chrome không khả dụng: {e}")

        # Thử Brave cuối cùng
        try:
            return _create_brave_driver()
        except Exception as e:
            print(f"Brave không khả dụng: {e}")

        raise Exception("Không thể khởi tạo bất kỳ trình duyệt nào! Vui lòng cài đặt Edge, Firefox, Chrome hoặc Brave.")

def _create_edge_driver():
    """Tạo Edge WebDriver"""
    edge_options = EdgeOptions()
    # Không sử dụng headless
    edge_options.add_argument('--disable-blink-features=AutomationControlled')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument('--disable-web-security')
    edge_options.add_argument('--allow-running-insecure-content')

    driver = webdriver.Edge(options=edge_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("✓ Đã khởi tạo Microsoft Edge")
    return driver

def _create_firefox_driver():
    """Tạo Firefox WebDriver"""
    firefox_options = FirefoxOptions()
    # Không sử dụng headless
    firefox_options.set_preference("dom.webdriver.enabled", False)
    firefox_options.set_preference('useAutomationExtension', False)

    driver = webdriver.Firefox(options=firefox_options)
    print("✓ Đã khởi tạo Mozilla Firefox")
    return driver

def _create_chrome_driver():
    """Tạo Chrome WebDriver"""
    chrome_options = Options()
    # Không sử dụng headless - để hiển thị trình duyệt
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("✓ Đã khởi tạo Google Chrome")
    return driver

def _create_brave_driver():
    """Tạo Brave WebDriver"""
    import os

    # Tìm đường dẫn Brave Browser
    brave_paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Users\{}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe".format(os.getenv('USERNAME')),
    ]

    brave_path = None
    for path in brave_paths:
        if os.path.exists(path):
            brave_path = path
            break

    if not brave_path:
        raise Exception("Không tìm thấy Brave Browser. Vui lòng cài đặt Brave hoặc kiểm tra đường dẫn.")

    # Sử dụng Chrome options với binary_location là Brave
    brave_options = Options()
    brave_options.binary_location = brave_path
    # Không sử dụng headless - để hiển thị trình duyệt
    brave_options.add_argument('--disable-blink-features=AutomationControlled')
    brave_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    brave_options.add_experimental_option('useAutomationExtension', False)
    brave_options.add_argument('--disable-web-security')
    brave_options.add_argument('--allow-running-insecure-content')

    driver = webdriver.Chrome(options=brave_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("✓ Đã khởi tạo Brave Browser")
    return driver

def decode_content(encoded_content):
    """Thử decode nội dung bằng nhiều phương pháp"""
    try:
        # Bước 1: Decode base64
        decoded_bytes = base64.b64decode(encoded_content)

        # Bước 2: Thử XOR với các key đơn giản
        for key_byte in range(1, 256):
            try:
                xor_result = bytes([b ^ key_byte for b in decoded_bytes])
                content = xor_result.decode('utf-8')
                if len(content) > 100 and any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có']):
                    print(f"XOR key found: {key_byte}")
                    return content
            except:
                continue

        # Bước 3: Thử Caesar cipher trên từng byte
        for shift in range(1, 256):
            try:
                shifted_result = bytes([(b + shift) % 256 for b in decoded_bytes])
                content = shifted_result.decode('utf-8')
                if len(content) > 100 and any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có']):
                    print(f"Caesar shift found: {shift}")
                    return content
            except:
                continue

        # Bước 4: Thử reverse bytes
        try:
            reversed_bytes = decoded_bytes[::-1]
            content = reversed_bytes.decode('utf-8')
            if len(content) > 100 and any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có']):
                print("Reverse bytes worked")
                return content
        except:
            pass

        # Bước 5: Thử decompress với gzip
        try:
            content = gzip.decompress(decoded_bytes).decode('utf-8')
            return content
        except:
            pass

        # Bước 6: Thử decompress với zlib
        try:
            content = zlib.decompress(decoded_bytes).decode('utf-8')
            return content
        except:
            pass

        # Bước 7: Thử AES decrypt với các key phổ biến
        try:
            possible_keys = [
                b'metruyencv12345',  # 16 bytes
                b'1234567890123456',  # 16 bytes
                b'abcdef1234567890',  # 16 bytes
                b'metruyencv123456789012345678901234',  # 32 bytes
            ]

            for key in possible_keys:
                try:
                    if len(key) >= 16:
                        cipher = AES.new(key[:16], AES.MODE_ECB)
                        decrypted = cipher.decrypt(decoded_bytes[:len(decoded_bytes)//16*16])
                        content = decrypted.decode('utf-8', errors='ignore').strip('\x00')
                        if len(content) > 50 and any(word in content for word in ['Tiểu', 'thế', 'người']):
                            return content
                except:
                    continue
        except ImportError:
            pass
        except:
            pass

        # Bước 8: Thử decode trực tiếp UTF-8
        try:
            content = decoded_bytes.decode('utf-8')
            return content
        except:
            pass

        # Bước 9: Thử decode latin-1 (fallback)
        try:
            content = decoded_bytes.decode('latin-1')
            if len(content) > 50:
                return content
        except:
            pass

    except Exception as e:
        print(f"Lỗi decode: {e}")

    return None

def login_to_site(driver, username, password, max_retries=3):
    """Đăng nhập vào MeTruyenCV"""

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"Đang thử đăng nhập lần {attempt + 1}/{max_retries}...")
            else:
                print("Đang thực hiện đăng nhập...")

            # Đợi trang load hoàn toàn
            time.sleep(3)

            # Thử tìm form đăng nhập trực tiếp trước
            login_form_found = False

            # Tìm form đăng nhập có sẵn trên trang
            username_selectors = [
                "//input[@name='username']",
                "//input[@name='email']",
                "//input[@type='email']",
                "//input[@placeholder*='email']",
                "//input[@placeholder*='tên']",
                "//input[@id='username']",
                "//input[@id='email']",
                "//input[@class*='username']",
                "//input[@class*='email']"
            ]

            username_field = None
            for selector in username_selectors:
                try:
                    username_field = driver.find_element(By.XPATH, selector)
                    if username_field.is_displayed() and username_field.is_enabled():
                        login_form_found = True
                        print("✓ Tìm thấy form đăng nhập trực tiếp")
                        break
                except:
                    continue

            # Nếu không tìm thấy form, tìm nút đăng nhập
            if not login_form_found:
                print("Đang tìm nút đăng nhập...")
                login_button = None
                try:
                    # Thử tìm các selector khác nhau cho nút đăng nhập
                    login_selectors = [
                        "//a[contains(text(), 'Đăng nhập')]",
                        "//a[contains(text(), 'Login')]",
                        "//button[contains(text(), 'Đăng nhập')]",
                        "//button[contains(text(), 'Login')]",
                        "//a[@href*='login']",
                        "//a[@href*='dang-nhap']",
                        "//span[contains(text(), 'Đăng nhập')]",
                        "//div[contains(text(), 'Đăng nhập')]",
                        "//a[contains(@class, 'login')]",
                        "//button[contains(@class, 'login')]"
                    ]

                    for selector in login_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    login_button = element
                                    print(f"✓ Tìm thấy nút đăng nhập: {selector}")
                                    break
                            if login_button:
                                break
                        except:
                            continue

                    if not login_button:
                        print("⚠️  Không tìm thấy nút đăng nhập, có thể đã đăng nhập rồi")
                        return True

                except Exception as e:
                    print(f"⚠️  Không tìm thấy nút đăng nhập: {e}")
                    return True

                # Click vào nút đăng nhập
                try:
                    driver.execute_script("arguments[0].click();", login_button)
                    time.sleep(3)
                    print("✓ Đã click nút đăng nhập")
                except Exception as e:
                    print(f"❌ Lỗi khi click nút đăng nhập: {e}")
                    return False

            # Tìm và điền username (tìm lại nếu chưa có)
            if not username_field:
                username_selectors = [
                    "//input[@name='username']",
                    "//input[@name='email']",
                    "//input[@type='email']",
                    "//input[@placeholder*='email']",
                    "//input[@placeholder*='tên']",
                    "//input[@id='username']",
                    "//input[@id='email']",
                    "//input[@class*='username']",
                    "//input[@class*='email']"
                ]

                for selector in username_selectors:
                    try:
                        username_field = driver.find_element(By.XPATH, selector)
                        if username_field.is_displayed() and username_field.is_enabled():
                            break
                    except:
                        continue

            if not username_field:
                print("❌ Không tìm thấy trường username/email")
                if attempt < max_retries - 1:
                    continue
                return False

            try:
                # Scroll đến element và đảm bảo nó visible
                driver.execute_script("arguments[0].scrollIntoView(true);", username_field)
                time.sleep(1)

                # Clear và điền username
                username_field.clear()
                username_field.send_keys(username)
                print("✓ Đã điền username")
            except Exception as e:
                print(f"❌ Lỗi khi điền username: {e}")
                if attempt < max_retries - 1:
                    continue
                return False

            # Tìm và điền password
            password_field = None
            password_selectors = [
                "//input[@name='password']",
                "//input[@type='password']",
                "//input[@id='password']",
                "//input[@class*='password']"
            ]

            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.XPATH, selector)
                    if password_field.is_displayed() and password_field.is_enabled():
                        break
                except:
                    continue

            if not password_field:
                print("❌ Không tìm thấy trường password")
                if attempt < max_retries - 1:
                    continue
                return False

            try:
                # Scroll đến element và đảm bảo nó visible
                driver.execute_script("arguments[0].scrollIntoView(true);", password_field)
                time.sleep(1)

                # Clear và điền password
                password_field.clear()
                password_field.send_keys(password)
                print("✓ Đã điền password")
            except Exception as e:
                print(f"❌ Lỗi khi điền password: {e}")
                if attempt < max_retries - 1:
                    continue
                return False

            # Tìm và click nút submit
            submit_button = None
            submit_selectors = [
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(), 'Đăng nhập')]",
                "//button[contains(text(), 'Login')]",
                "//input[@value='Đăng nhập']",
                "//input[@value='Login']",
                "//button[contains(@class, 'submit')]",
                "//button[contains(@class, 'login')]",
                "//a[contains(@class, 'submit')]"
            ]

            for selector in submit_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            submit_button = element
                            break
                    if submit_button:
                        break
                except:
                    continue

            if not submit_button:
                print("❌ Không tìm thấy nút submit")
                # Thử submit bằng Enter
                try:
                    password_field.send_keys("\n")
                    time.sleep(3)
                    print("✓ Đã thử submit bằng Enter")
                except:
                    if attempt < max_retries - 1:
                        continue
                    return False
            else:
                try:
                    # Scroll đến nút submit
                    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                    time.sleep(1)

                    # Click submit
                    driver.execute_script("arguments[0].click();", submit_button)
                    time.sleep(3)
                    print("✓ Đã click nút submit")
                except Exception as e:
                    print(f"❌ Lỗi khi click submit: {e}")
                    if attempt < max_retries - 1:
                        continue
                    return False

            # Kiểm tra đăng nhập thành công
            # Tìm các dấu hiệu đăng nhập thành công
            success_indicators = [
                "//a[contains(text(), 'Đăng xuất')]",
                "//a[contains(text(), 'Logout')]",
                "//a[contains(text(), 'Tài khoản')]",
                "//a[contains(text(), 'Profile')]",
                "//span[contains(@class, 'user')]",
                "//div[contains(@class, 'user')]"
            ]

            for indicator in success_indicators:
                try:
                    element = driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        print("✓ Đăng nhập thành công!")
                        return True
                except:
                    continue

            print("⚠️  Không thể xác nhận đăng nhập thành công, tiếp tục...")
            return True

        except Exception as e:
            print(f"❌ Lỗi khi đăng nhập (lần {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("Đang thử lại...")
                time.sleep(2)
                continue
            else:
                print("❌ Đã thử tối đa số lần cho phép")
                return False

    return False

def load_config():
    """Đọc cấu hình từ config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except:
        print("Không tìm thấy config.json!")
        return None

def get_story_info(story_url, driver=None, browser_choice="auto", login_config=None):
    """Lấy thông tin truyện sử dụng Selenium"""
    driver_created = False
    try:
        if driver is None:
            driver = create_driver(browser_choice)
            driver_created = True

        print("Đang tải trang truyện...")
        driver.get(story_url)

        # Thực hiện đăng nhập nếu được cấu hình
        if login_config and login_config.get('enabled', False):
            username = login_config.get('username', '')
            password = login_config.get('password', '')
            max_retries = login_config.get('max_retries', 3)
            if username and password:
                login_to_site(driver, username, password, max_retries)

        # Đợi trang load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        # Lấy tên truyện
        try:
            title_element = driver.find_element(By.TAG_NAME, "h1")
            story_title = title_element.text.strip()
        except:
            story_title = "Unknown_Story"

        # Tạo thư mục
        safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip()
        story_folder = safe_title.replace(" ", "_")
        os.makedirs(story_folder, exist_ok=True)

        print(f"Tên truyện: {story_title}")
        print(f"Thư mục: {story_folder}")

        return story_folder

    except Exception as e:
        print(f"Lỗi khi lấy thông tin truyện: {e}")
        return None
    finally:
        if driver_created and driver:
            driver.quit()

def get_chapters(story_url, driver=None, browser_choice="auto", login_config=None):
    """Lấy danh sách chương sử dụng Selenium"""
    driver_created = False
    try:
        if driver is None:
            driver = create_driver(browser_choice)
            driver_created = True

        print("Đang tải trang truyện...")
        driver.get(story_url)

        # Đợi trang load
        time.sleep(3)

        # Lấy slug từ URL
        slug = story_url.split('/')[-1]  # tan-the-chi-sieu-thi-he-thong

        # Thử tìm nút "Đọc Truyện" hoặc link chương đầu tiên
        chapters = []

        try:
            # Tìm nút đọc truyện
            read_buttons = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'chuong-1')] | //a[contains(@href, 'chuong-1')]")

            if read_buttons:
                # Lấy URL chương đầu tiên
                button = read_buttons[0]
                if button.tag_name == 'button':
                    onclick = button.get_attribute('onclick')
                    if 'location.href=' in onclick:
                        first_chapter_url = onclick.split("'")[1]
                        print(f"Tìm thấy chương đầu từ nút: {first_chapter_url}")
                else:
                    first_chapter_url = button.get_attribute('href')
                    print(f"Tìm thấy chương đầu từ link: {first_chapter_url}")

                # Tạo danh sách chương từ URL này
                if 'chuong-1' in first_chapter_url:
                    base_url = first_chapter_url.rsplit('/chuong-', 1)[0]
                    for i in range(1, 609):  # Tạo 608 chương
                        chapter_url = f"{base_url}/chuong-{i}"
                        chapter_title = f"Chương {i}"
                        chapters.append({"title": chapter_title, "url": chapter_url})

                    print(f"Đã tạo {len(chapters)} chương từ pattern")

            # Nếu không tìm thấy, thử pattern mặc định
            if not chapters:
                print("Không tìm thấy nút đọc, sử dụng pattern mặc định...")
                for i in range(1, 609):
                    chapter_url = f"https://metruyencv.com/truyen/{slug}/chuong-{i}"
                    chapter_title = f"Chương {i}"
                    chapters.append({"title": chapter_title, "url": chapter_url})

                print(f"Đã tạo {len(chapters)} chương từ pattern mặc định")

            # Test chương đầu tiên sử dụng driver hiện tại
            if chapters:
                print("Đang test chương đầu tiên...")
                try:
                    driver.get(chapters[0]['url'])
                    time.sleep(2)

                    # Kiểm tra xem có chapterData không
                    scripts = driver.find_elements(By.TAG_NAME, "script")
                    has_chapter_data = False

                    for script in scripts:
                        script_content = driver.execute_script("return arguments[0].innerHTML;", script)
                        if script_content and 'chapterData' in script_content:
                            has_chapter_data = True
                            break

                    if has_chapter_data:
                        print("✓ Pattern URL hoạt động và có chapterData!")
                    else:
                        print("⚠️  Pattern URL hoạt động nhưng không có chapterData")

                except Exception as e:
                    print(f"✗ Lỗi khi test chương đầu: {e}")

        except Exception as e:
            print(f"Lỗi khi tìm chương: {e}")
            # Fallback: tạo pattern mặc định
            for i in range(1, 609):
                chapter_url = f"https://metruyencv.com/truyen/{slug}/chuong-{i}"
                chapter_title = f"Chương {i}"
                chapters.append({"title": chapter_title, "url": chapter_url})

            print(f"Đã tạo {len(chapters)} chương từ fallback pattern")

        return chapters

    except Exception as e:
        print(f"Lỗi khi lấy danh sách chương: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver_created and driver:
            driver.quit()

def download_chapter(chapter_url, chapter_title, story_folder, driver=None, browser_choice="auto", login_config=None):
    """Tải một chương sử dụng Selenium"""
    driver_created = False
    try:
        if driver is None:
            driver = create_driver(browser_choice)
            driver_created = True

        print(f"Đang tải: {chapter_title}")
        driver.get(chapter_url)

        # Đợi trang load
        time.sleep(3)

        # Tìm nội dung từ JavaScript data
        scripts = driver.find_elements(By.TAG_NAME, "script")
        content = None

        for script in scripts:
            try:
                script_text = driver.execute_script("return arguments[0].innerHTML;", script)
                if script_text and 'window.chapterData' in script_text:
                    # Extract content từ JavaScript
                    # Tìm phần textlinks trong chapterData
                    textlinks_match = re.search(r'textlinks:\s*\[(.*?)\]', script_text, re.DOTALL)
                    if textlinks_match:
                        textlinks_str = textlinks_match.group(1)

                        # Extract tất cả code content từ textlinks
                        code_matches = re.findall(r'"code":"([^"]*)"', textlinks_str)

                        if code_matches:
                            # Ghép tất cả nội dung lại
                            full_content = ""
                            for code_content in code_matches:
                                # Decode escape sequences
                                decoded_code = code_content.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')

                                # Decode Unicode escape sequences
                                try:
                                    import codecs

                                    def decode_unicode_match(match):
                                        try:
                                            return codecs.decode(match.group(0), 'unicode_escape')
                                        except:
                                            return match.group(0)

                                    # Tìm tất cả Unicode escape sequences và decode chúng
                                    decoded_code = re.sub(r'\\u[0-9a-fA-F]{4}', decode_unicode_match, decoded_code)

                                except Exception as e:
                                    print(f"Lỗi decode Unicode: {e}")
                                    pass

                                # Loại bỏ HTML tags
                                clean_code = re.sub(r'<[^>]+>', '', decoded_code)

                                # Loại bỏ dấu gạch ngang đầu
                                clean_code = re.sub(r'^-+\s*', '', clean_code.strip())

                                if clean_code.strip():
                                    full_content += clean_code.strip() + "\n\n"

                            if full_content.strip():
                                content = full_content.strip()
                                print(f"✓ Lấy được nội dung từ textlinks ({len(content)} ký tự)")
                                break

                    # Fallback: thử decode content cũ nếu không tìm thấy textlinks
                    if not content:
                        content_match = re.search(r'content:\s*"([^"]+)"', script_text)
                        if content_match:
                            encoded_content = content_match.group(1)
                            content = decode_content(encoded_content)
                            if content:
                                print(f"✓ Decode content thành công ({len(content)} ký tự)")
                                break
                            else:
                                print(f"❌ Không thể decode content")

            except Exception as e:
                print(f"Lỗi khi extract content: {e}")
                continue

        if not content:
            print(f"Không tìm thấy nội dung trong JavaScript: {chapter_title}")
            return False

        if len(content) < 50:
            print(f"Nội dung quá ngắn ({len(content)} ký tự): {chapter_title}")
            return False

        # Tạo tên file an toàn
        safe_title = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.txt"
        filepath = os.path.join(story_folder, filename)

        # Lưu file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{chapter_title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(content)

        # Kiểm tra xem nội dung có bị mã hóa không
        if len(content) < 500 or not any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có', 'là', 'của']):
            print(f"⚠️  Đã tải: {chapter_title} ({len(content)} ký tự) - Nội dung có thể vẫn bị mã hóa")
        else:
            print(f"✓ Đã tải: {chapter_title} ({len(content)} ký tự)")
        return True

    except Exception as e:
        print(f"✗ Lỗi khi tải {chapter_title}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver_created and driver:
            driver.quit()

def main():
    """Hàm chính"""
    print("=== MeTruyenCV Downloader (Ultra Simple) ===")

    # Đọc cấu hình
    config = load_config()
    if not config:
        return

    # Lấy thông tin từ config
    account_config = config.get("account", {})
    download_config = config.get("download", {})
    settings_config = config.get("settings", {})

    story_url = download_config.get("story_url", "")
    start_chapter = download_config.get("start_chapter", 1)
    end_chapter = download_config.get("end_chapter", -1)

    username = account_config.get("username", "")
    password = account_config.get("password", "")

    # Lấy cấu hình từ settings
    browser_choice = settings_config.get("browser", "auto")
    delay_between_chapters = settings_config.get("delay_between_chapters", 2)
    max_retries = settings_config.get("max_retries", 3)
    output_folder = download_config.get("output_folder", "downloads")

    # Kiểm tra thông tin cần thiết
    if not story_url:
        print("❌ Vui lòng nhập story_url trong config.json!")
        print("Ví dụ: https://metruyencv.com/truyen/ten-truyen")
        return

    if not username or not password:
        print("❌ Vui lòng nhập username và password trong config.json!")
        return

    print(f"URL: {story_url}")
    print(f"Chương: {start_chapter} đến {end_chapter if end_chapter > 0 else 'cuối'}")
    print(f"Tài khoản: {username}")
    print(f"Trình duyệt: {browser_choice}")
    print(f"Thư mục lưu: {output_folder}")
    print(f"Delay giữa các chương: {delay_between_chapters}s")

    # Tạo login_config cho các hàm khác
    login_config = {
        'enabled': True,
        'username': username,
        'password': password,
        'max_retries': max_retries
    }

    # Tạo WebDriver một lần duy nhất
    driver = None
    try:
        driver = create_driver(browser_choice)

        # Tạo thư mục output nếu chưa có
        if output_folder and output_folder != "downloads":
            os.makedirs(output_folder, exist_ok=True)
            os.chdir(output_folder)

        # Lấy thông tin truyện
        story_folder = get_story_info(story_url, driver, browser_choice, login_config)
        if not story_folder:
            return

        # Lấy danh sách chương
        chapters = get_chapters(story_url, driver, browser_choice, login_config)
        if not chapters:
            print("Không tìm thấy chương nào!")
            return

        # Xác định phạm vi tải
        if end_chapter and end_chapter <= len(chapters):
            chapters_to_download = chapters[start_chapter-1:end_chapter]
        else:
            chapters_to_download = chapters[start_chapter-1:]

        print(f"Sẽ tải {len(chapters_to_download)} chương")

        # Tải từng chương
        success = 0
        for i, chapter in enumerate(chapters_to_download, 1):
            print(f"[{i}/{len(chapters_to_download)}] Đang tải: {chapter['title']}")

            if download_chapter(chapter['url'], chapter['title'], story_folder, driver, browser_choice, login_config):
                success += 1

            time.sleep(delay_between_chapters)  # Nghỉ theo cấu hình
    finally:
        # Đóng WebDriver khi hoàn thành
        if driver:
            try:
                driver.quit()
                print("✓ Đã đóng trình duyệt")
            except:
                pass
    
    print(f"\nHoàn thành! Đã tải {success}/{len(chapters_to_download)} chương")
    print(f"Truyện được lưu trong thư mục: {story_folder}")

    if success > 0:
        print("\n" + "="*50)
        print("📝 LƯU Ý VỀ NỘI DUNG:")
        print("- Nếu thấy ký tự lạ trong file txt, nội dung có thể vẫn bị mã hóa")
        print("- Trang web sử dụng thuật toán mã hóa phức tạp")
        print("- Dự án đã tải được cấu trúc chương thành công")
        print("- Có thể cần reverse engineering thêm để giải mã hoàn toàn")
        print("="*50)

if __name__ == "__main__":
    main()
