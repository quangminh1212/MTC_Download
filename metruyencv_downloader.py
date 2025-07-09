#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader
Tải truyện từ metruyencv.com và lưu thành file txt theo từng chương
"""

import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MeTruyenCVDownloader:
    def __init__(self, headless=True):
        """
        Khởi tạo downloader
        Args:
            headless (bool): Chạy browser ở chế độ headless hay không
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        self.setup_driver()
    
    def setup_driver(self):
        """Thiết lập Chrome driver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("Chrome driver đã được thiết lập thành công")
        except Exception as e:
            logger.error(f"Lỗi khi thiết lập driver: {e}")
            raise
    
    def get_story_info(self, story_url):
        """
        Lấy thông tin truyện từ URL
        Args:
            story_url (str): URL của truyện
        Returns:
            dict: Thông tin truyện
        """
        try:
            self.driver.get(story_url)
            time.sleep(2)
            
            # Lấy tên truyện
            title_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'title') or contains(@class, 'story-title')]"))
            )
            story_title = title_element.text.strip()
            
            # Lấy tác giả
            try:
                author_element = self.driver.find_element(By.XPATH, "//a[contains(@href, '/tac-gia/')]")
                author = author_element.text.strip()
            except:
                author = "Không rõ"
            
            # Tạo thư mục lưu truyện
            safe_title = self.sanitize_filename(story_title)
            story_dir = os.path.join("truyen", safe_title)
            os.makedirs(story_dir, exist_ok=True)
            
            logger.info(f"Tên truyện: {story_title}")
            logger.info(f"Tác giả: {author}")
            logger.info(f"Thư mục lưu: {story_dir}")
            
            return {
                "title": story_title,
                "author": author,
                "directory": story_dir,
                "url": story_url
            }
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông tin truyện: {e}")
            raise
    
    def get_chapter_list(self, story_url):
        """
        Lấy danh sách các chương
        Args:
            story_url (str): URL của truyện
        Returns:
            list: Danh sách các chương với URL và tên
        """
        try:
            self.driver.get(story_url)
            time.sleep(2)
            
            # Tìm nút "Mục Lục" hoặc danh sách chương
            try:
                # Thử tìm nút mục lục
                muc_luc_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Mục Lục') or contains(text(), 'Danh sách chương')]")
                muc_luc_button.click()
                time.sleep(2)
            except:
                logger.info("Không tìm thấy nút Mục Lục, tìm danh sách chương trực tiếp")
            
            # Tìm danh sách chương
            chapter_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/chuong-')]")
            
            chapters = []
            for element in chapter_elements:
                chapter_url = element.get_attribute("href")
                chapter_title = element.text.strip()
                if chapter_url and chapter_title:
                    chapters.append({
                        "title": chapter_title,
                        "url": chapter_url
                    })
            
            logger.info(f"Tìm thấy {len(chapters)} chương")
            return chapters
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách chương: {e}")
            return []
    
    def download_chapter(self, chapter_url, chapter_title, story_dir):
        """
        Tải nội dung một chương
        Args:
            chapter_url (str): URL của chương
            chapter_title (str): Tên chương
            story_dir (str): Thư mục lưu truyện
        Returns:
            bool: True nếu tải thành công
        """
        try:
            self.driver.get(chapter_url)
            time.sleep(2)
            
            # Tìm nội dung chương
            content_selectors = [
                "//div[@id='chapter-content']",
                "//div[contains(@class, 'chapter-content')]",
                "//div[contains(@class, 'content')]",
                "//div[contains(@class, 'story-content')]"
            ]
            
            content_element = None
            for selector in content_selectors:
                try:
                    content_element = self.driver.find_element(By.XPATH, selector)
                    break
                except:
                    continue
            
            if not content_element:
                logger.warning(f"Không tìm thấy nội dung cho chương: {chapter_title}")
                return False
            
            # Lấy nội dung text
            content = content_element.text.strip()
            
            # Tạo tên file an toàn
            safe_chapter_title = self.sanitize_filename(chapter_title)
            file_path = os.path.join(story_dir, f"{safe_chapter_title}.txt")
            
            # Lưu file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{chapter_title}\n")
                f.write("=" * len(chapter_title) + "\n\n")
                f.write(content)
            
            logger.info(f"Đã tải: {chapter_title}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi tải chương {chapter_title}: {e}")
            return False
    
    def sanitize_filename(self, filename):
        """
        Làm sạch tên file để có thể lưu được
        Args:
            filename (str): Tên file gốc
        Returns:
            str: Tên file đã được làm sạch
        """
        # Loại bỏ các ký tự không hợp lệ
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.strip()
        return filename[:200]  # Giới hạn độ dài tên file
    
    def download_story(self, story_url, start_chapter=1, end_chapter=None):
        """
        Tải toàn bộ truyện
        Args:
            story_url (str): URL của truyện
            start_chapter (int): Chương bắt đầu (mặc định 1)
            end_chapter (int): Chương kết thúc (None = tất cả)
        """
        try:
            # Lấy thông tin truyện
            story_info = self.get_story_info(story_url)
            
            # Lấy danh sách chương
            chapters = self.get_chapter_list(story_url)
            
            if not chapters:
                logger.error("Không tìm thấy chương nào")
                return
            
            # Xác định phạm vi tải
            if end_chapter is None:
                end_chapter = len(chapters)
            
            chapters_to_download = chapters[start_chapter-1:end_chapter]
            
            logger.info(f"Bắt đầu tải {len(chapters_to_download)} chương...")
            
            success_count = 0
            for i, chapter in enumerate(chapters_to_download, 1):
                logger.info(f"Đang tải chương {i}/{len(chapters_to_download)}: {chapter['title']}")
                
                if self.download_chapter(chapter['url'], chapter['title'], story_info['directory']):
                    success_count += 1
                
                # Nghỉ giữa các lần tải để tránh bị chặn
                time.sleep(1)
            
            logger.info(f"Hoàn thành! Đã tải thành công {success_count}/{len(chapters_to_download)} chương")
            logger.info(f"Truyện được lưu tại: {story_info['directory']}")
            
        except Exception as e:
            logger.error(f"Lỗi khi tải truyện: {e}")
        finally:
            self.close()
    
    def close(self):
        """Đóng browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Đã đóng browser")

def main():
    """Hàm main"""
    # URL truyện cần tải
    story_url = "https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong"
    
    # Tạo downloader
    downloader = MeTruyenCVDownloader(headless=False)  # Đặt True để chạy headless
    
    try:
        # Tải truyện (có thể chỉ định phạm vi chương)
        downloader.download_story(story_url, start_chapter=1, end_chapter=10)  # Tải 10 chương đầu
        # downloader.download_story(story_url)  # Tải toàn bộ truyện
    except KeyboardInterrupt:
        logger.info("Người dùng dừng chương trình")
    except Exception as e:
        logger.error(f"Lỗi: {e}")
    finally:
        downloader.close()

if __name__ == "__main__":
    main()
