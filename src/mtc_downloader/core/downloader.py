#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module chứa các chức năng tải truyện từ metruyencv.com
"""

import os
import re
import requests
from bs4 import BeautifulSoup
import time
import random
import logging

# Thiết lập logging
logger = logging.getLogger(__name__)

def download_chapter(url, output_file=None, delay=1):
    """
    Tải một chương truyện từ URL của metruyencv.com và lưu thành file text
    
    Args:
        url: URL của chương truyện (ví dụ: https://metruyencv.com/truyen/ten-truyen/chuong-XX)
        output_file: Đường dẫn file đầu ra để lưu nội dung
        delay: Thời gian chờ giữa các request (giây)
    
    Returns:
        Đường dẫn file output hoặc None nếu thất bại
    """
    # Kiểm tra URL
    if not url.startswith("https://metruyencv.com/truyen/"):
        logger.error(f"URL không hợp lệ: {url}")
        logger.error("URL phải có dạng: https://metruyencv.com/truyen/ten-truyen/chuong-XX")
        return None
    
    try:
        # Tải nội dung trang
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        logger.info(f"Đang tải chương từ URL: {url}")
        response = requests.get(url, headers=headers)
        
        # Kiểm tra response
        if response.status_code != 200:
            logger.error(f"Lỗi khi tải trang: {response.status_code}")
            return None
        
        # Phân tích HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm tiêu đề chương
        chapter_title = soup.select_one("h2.text-center.text-gray-600")
        story_title = soup.select_one("h1.text-lg.text-center a.text-title")
        
        # Nếu không tìm thấy theo cách thông thường, thử các cách khác
        if not chapter_title:
            chapter_title = soup.select_one("h2") or soup.select_one("h1.chapter-title")
        
        if not story_title:
            story_title = soup.select_one("h1 a") or soup.select_one("title")
        
        # Extract text from elements
        title_text = chapter_title.text.strip() if chapter_title else "Unknown Chapter"
        story_name = story_title.text.strip() if story_title else "Unknown Story"
        
        # Tìm phần tử chứa nội dung chính
        story_content = soup.select_one("div#chapter-content") or soup.select_one("div.chapter-content")
        
        if not story_content:
            logger.error(f"Không tìm thấy nội dung chương trong trang!")
            return None
        
        # Lấy văn bản từ nội dung
        text = story_content.get_text(separator="\n\n", strip=True)
        
        # Xóa các nội dung quảng cáo
        text = re.sub(r'-----.*?-----', '', text, flags=re.DOTALL)
        
        # Tạo nội dung đầy đủ với tiêu đề
        full_content = f"{story_name}\n\n{title_text}\n\n{'='*50}\n\n{text}"
        
        # Nếu không chỉ định output_file, tự tạo tên file
        if output_file is None:
            # Tạo tên file từ tiêu đề chương, loại bỏ các ký tự không hợp lệ
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title_text)
            output_file = f"{safe_title}.txt"
        
        # Ghi nội dung vào file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Đã lưu nội dung chương vào file: {output_file}")
        
        return output_file
    
    except Exception as e:
        logger.exception(f"Lỗi khi tải chương: {str(e)}")
        return None

def download_multiple_chapters(start_url, num_chapters=1, output_dir=None, delay=1, combine=False):
    """
    Tải nhiều chương truyện liên tiếp từ URL bắt đầu
    
    Args:
        start_url: URL của chương đầu tiên
        num_chapters: Số lượng chương cần tải (tính từ chương đầu tiên)
        output_dir: Thư mục để lưu các file
        delay: Thời gian chờ giữa các request (giây)
        combine: Ghép tất cả các chương vào một file
    
    Returns:
        Số lượng chương đã tải thành công
    """
    if not start_url.startswith("https://metruyencv.com/truyen/"):
        logger.error(f"URL không hợp lệ: {start_url}")
        logger.error("URL phải có dạng: https://metruyencv.com/truyen/ten-truyen/chuong-XX")
        return 0
    
    # Đảm bảo output_dir tồn tại
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    successful = 0
    output_files = []
    current_url = start_url
    
    # Extract base URL và pattern cho chương tiếp theo
    match = re.search(r'(https://metruyencv.com/truyen/[^/]+/chuong-)(\d+)', start_url)
    if not match:
        logger.error("Không thể xác định định dạng URL chương")
        return 0
    
    base_url = match.group(1)
    start_chapter = int(match.group(2))
    
    for i in range(num_chapters):
        chapter_number = start_chapter + i
        current_url = f"{base_url}{chapter_number}"
        
        logger.info(f"Đang tải chương {chapter_number} ({i+1}/{num_chapters})")
        
        # Xác định file đầu ra
        if output_dir:
            output_file = os.path.join(output_dir, f"Chương_{chapter_number}.txt")
        else:
            output_file = None
        
        # Tải chương
        result = download_chapter(current_url, output_file, delay)
        
        if result:
            successful += 1
            output_files.append(result)
            
            # Thêm độ trễ để tránh bị chặn
            delay_time = delay + random.uniform(0.5, 1.5)
            logger.info(f"Đợi {delay_time:.2f} giây trước khi tải chương tiếp theo...")
            time.sleep(delay_time)
        else:
            logger.error(f"Không thể tải chương {chapter_number}, đang dừng quá trình tải")
            break
    
    # Kết hợp tất cả file nếu được yêu cầu
    if combine and output_files:
        if output_dir:
            combined_file = os.path.join(output_dir, "combined_story.txt")
        else:
            combined_file = "combined_story.txt"
            
        with open(combined_file, 'w', encoding='utf-8') as outfile:
            for output_file in output_files:
                with open(output_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n" + "="*50 + "\n\n")  # Dấu phân cách giữa các chương
        
        logger.info(f"Đã kết hợp {len(output_files)} chương vào {combined_file}")
    
    return successful

def download_all_chapters(url, output_dir=None, delay=1, combine=False):
    """
    Tải tất cả các chương của một truyện
    
    Args:
        url: URL của truyện hoặc một chương bất kỳ
        output_dir: Thư mục để lưu các file
        delay: Thời gian chờ giữa các request (giây)
        combine: Ghép tất cả các chương vào một file
    
    Returns:
        Số lượng chương đã tải thành công
    """
    # Chuẩn hóa URL truyện
    if "/chuong-" in url:
        # Nếu là URL của chương, chuyển thành URL của truyện
        story_url = re.sub(r'/chuong-\d+', '', url)
    elif not url.endswith('/'):
        story_url = url + "/"
    else:
        story_url = url
    
    try:
        # Tải trang truyện để lấy thông tin về số chương
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        logger.info(f"Đang tải thông tin truyện từ: {story_url}")
        response = requests.get(story_url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Lỗi khi tải trang truyện: {response.status_code}")
            return 0
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm tên truyện để đặt tên thư mục
        story_title_elem = soup.select_one("h1.font-semibold") or soup.select_one("title")
        story_title = story_title_elem.text.strip() if story_title_elem else "Unknown_Story"
        safe_story_title = re.sub(r'[\\/*?:"<>|]', "", story_title)
        
        # Tạo thư mục nếu không được chỉ định
        if not output_dir:
            output_dir = safe_story_title
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
        
        # Tìm số chương mới nhất - thử nhiều loại selector khác nhau
        latest_chapter_elem = None
        num_chapters = 0
        
        # Thử các selector khác nhau để tìm thông tin chương mới nhất
        selectors = [
            "span.latest-chapter",  # Selector cũ
            ".text-base.font-semibold",  # Thử một selector mới
            "p:contains('Chương ')",  # Tìm thẻ p có chứa từ "Chương"
            ".chapter-nav a",  # Thử tìm trong menu điều hướng chương
            "a[href*='chuong-']",  # Tìm các link chương
            "a:contains('Chương ')"  # Tìm các link có chứa từ "Chương"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.text.strip()
                    # Tìm số chương từ text
                    match = re.search(r'[Cc]hương (\d+)', text)
                    if match:
                        current_chapter = int(match.group(1))
                        num_chapters = max(num_chapters, current_chapter)
                        latest_chapter_elem = element
                        break
                
                # Nếu đã tìm thấy thông tin chương, thoát khỏi vòng lặp
                if num_chapters > 0:
                    break
                    
        # Nếu vẫn không tìm thấy, thử tìm từ các URL chương trong trang
        if num_chapters == 0:
            chapter_links = soup.select("a[href*='/chuong-']")
            for link in chapter_links:
                href = link.get('href', '')
                match = re.search(r'/chuong-(\d+)', href)
                if match:
                    current_chapter = int(match.group(1))
                    num_chapters = max(num_chapters, current_chapter)
        
        # Nếu vẫn không tìm thấy, thử tìm từ các phần tử có chứa số chương
        if num_chapters == 0:
            all_elements = soup.select("*")
            for element in all_elements:
                if element.name in ['span', 'p', 'a', 'div']:
                    text = element.text.strip()
                    match = re.search(r'[Cc]hương (\d+)', text)
                    if match:
                        current_chapter = int(match.group(1))
                        num_chapters = max(num_chapters, current_chapter)
        
        # Nếu tất cả các cách trên đều thất bại, thử tải trang mục lục
        if num_chapters == 0:
            toc_url = f"{story_url}muc-luc"
            logger.info(f"Không tìm thấy thông tin chương từ trang chính, đang thử tải mục lục từ: {toc_url}")
            try:
                toc_response = requests.get(toc_url, headers=headers)
                if toc_response.status_code == 200:
                    toc_soup = BeautifulSoup(toc_response.content, 'html.parser')
                    chapter_links = toc_soup.select("a[href*='/chuong-']")
                    for link in chapter_links:
                        href = link.get('href', '')
                        match = re.search(r'/chuong-(\d+)', href)
                        if match:
                            current_chapter = int(match.group(1))
                            num_chapters = max(num_chapters, current_chapter)
            except Exception as e:
                logger.exception(f"Lỗi khi tải trang mục lục: {str(e)}")
        
        # Nếu vẫn không tìm được số chương, thử dùng hardcode số chương cụ thể
        if num_chapters == 0:
            logger.error("Không thể xác định số chương từ trang. Sử dụng số chương mặc định (10).")
            num_chapters = 10
        else:
            logger.info(f"Tổng số chương: {num_chapters}")
        
        # Tạo URL cho chương đầu tiên
        first_chapter_url = f"{story_url}chuong-1"
        
        # Tải tất cả các chương
        return download_multiple_chapters(first_chapter_url, num_chapters, output_dir, delay, combine)
        
    except Exception as e:
        logger.exception(f"Lỗi khi tải thông tin truyện: {str(e)}")
        return 0 