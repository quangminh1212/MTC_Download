#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader - Phiên bản đơn giản
Tải truyện từ metruyencv.com và lưu thành file txt
"""

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Thiết lập Chrome driver"""
    try:
        options = Options()
        options.add_argument("--headless")  # Chạy ẩn
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")

        # Thử dùng ChromeDriver local trước
        if os.path.exists("chromedriver.exe"):
            print("Sử dụng ChromeDriver local...")
            service = Service("chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=options)
            print("✓ ChromeDriver local đã sẵn sàng")
            return driver

        print("Đang tải ChromeDriver...")

        # Tự động tải ChromeDriver phù hợp
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        print("✓ ChromeDriver đã sẵn sàng")
        return driver

    except Exception as e:
        print(f"Lỗi khi thiết lập ChromeDriver: {e}")
        print("\nHướng dẫn khắc phục:")
        print("1. Chạy: python manual_chrome_setup.py")
        print("2. Hoặc chạy: python fix_chrome.py")
        print("3. Đảm bảo Google Chrome đã được cài đặt")
        return None

def get_story_title(driver):
    """Lấy tên truyện"""
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        return title
    except:
        return "Unknown_Story"

def get_chapters(driver):
    """Lấy danh sách chương"""
    chapters = []
    try:
        # Tìm tất cả link chương
        chapter_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/chuong-')]")
        
        for link in chapter_links:
            url = link.get_attribute("href")
            title = link.text.strip()
            if url and title:
                chapters.append({"title": title, "url": url})
        
        print(f"Tìm thấy {len(chapters)} chương")
        return chapters
    except Exception as e:
        print(f"Lỗi khi lấy danh sách chương: {e}")
        return []

def download_chapter(driver, chapter_url, chapter_title, story_folder):
    """Tải một chương"""
    try:
        driver.get(chapter_url)
        time.sleep(2)
        
        # Tìm nội dung chương
        content = ""
        selectors = [
            "//div[@id='chapter-content']",
            "//div[contains(@class, 'chapter-content')]",
            "//div[contains(@class, 'content')]"
        ]
        
        for selector in selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                content = element.text.strip()
                if content:
                    break
            except:
                continue
        
        if not content:
            print(f"Không tìm thấy nội dung: {chapter_title}")
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
        
        print(f"✓ Đã tải: {chapter_title}")
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi tải {chapter_title}: {e}")
        return False

def load_config():
    """Đọc cấu hình từ config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("Không tìm thấy file config.json!")
        return None
    except json.JSONDecodeError:
        print("File config.json không đúng định dạng!")
        return None

def main():
    """Hàm chính"""
    # Đọc cấu hình
    config = load_config()
    if not config:
        return

    story_url = config.get("story_url")
    start_chapter = config.get("start_chapter", 1)
    end_chapter = config.get("end_chapter")

    if not story_url:
        print("Không tìm thấy story_url trong config.json!")
        return

    print("Bắt đầu tải truyện...")
    print(f"URL: {story_url}")
    print(f"Chương: {start_chapter} đến {end_chapter if end_chapter else 'cuối'}")
    
    # Thiết lập driver
    driver = setup_driver()

    if not driver:
        print("Không thể khởi tạo ChromeDriver!")
        return

    try:
        # Truy cập trang truyện
        driver.get(story_url)
        time.sleep(3)
        
        # Lấy tên truyện
        story_title = get_story_title(driver)
        print(f"Tên truyện: {story_title}")
        
        # Tạo thư mục
        story_folder = story_title.replace(" ", "_")
        os.makedirs(story_folder, exist_ok=True)
        
        # Lấy danh sách chương
        chapters = get_chapters(driver)

        if not chapters:
            print("Không tìm thấy chương nào!")
            return

        # Xác định phạm vi tải
        if end_chapter and end_chapter <= len(chapters):
            chapters_to_download = chapters[start_chapter-1:end_chapter]
        else:
            chapters_to_download = chapters[start_chapter-1:]

        print(f"Sẽ tải {len(chapters_to_download)} chương (từ {start_chapter} đến {start_chapter + len(chapters_to_download) - 1})")

        # Tải từng chương
        success = 0
        for i, chapter in enumerate(chapters_to_download, 1):
            print(f"[{i}/{len(chapters_to_download)}] Đang tải: {chapter['title']}")

            if download_chapter(driver, chapter['url'], chapter['title'], story_folder):
                success += 1

            time.sleep(1)  # Nghỉ 1 giây
        
        print(f"\nHoàn thành! Đã tải {success}/{len(chapters_to_download)} chương")
        print(f"Truyện được lưu trong thư mục: {story_folder}")
        
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
