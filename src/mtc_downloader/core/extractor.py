#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module chứa các chức năng trích xuất nội dung từ file HTML
"""

import os
import re
import glob
from bs4 import BeautifulSoup
import logging

# Thiết lập logging
logger = logging.getLogger(__name__)

def extract_story_content(html_file, output_file=None):
    """
    Trích xuất nội dung truyện từ file HTML và lưu vào file text
    
    Args:
        html_file: Đường dẫn file HTML đầu vào
        output_file: Đường dẫn file text đầu ra. Nếu None, sẽ tự tạo tên file
    
    Returns:
        Đường dẫn file output hoặc None nếu thất bại
    """
    try:
        # Nếu không chỉ định output_file, tự tạo tên file từ html_file
        if output_file is None:
            # Thay đổi phần mở rộng từ .html sang .txt
            output_file = os.path.splitext(html_file)[0] + ".txt"
        
        # Đọc file HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Phân tích HTML bằng BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tìm thông tin tiêu đề, lần lượt thử các selector phổ biến
        title_selectors = [
            "h2.text-center.text-gray-600",  # Selector cũ
            "h1.font-semibold",              # Tiêu đề truyện
            "h2",                           # Tiêu đề chương
            "h1",                           # Thử tìm h1 đầu tiên
            "title",                        # Thử tìm trong title
            ".story-title",                 # Class tiêu đề truyện
            ".chapter-title"                # Class tiêu đề chương
        ]
        
        title_element = None
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element and title_element.text.strip():
                break
        
        # Tìm tiêu đề chương (h2) nếu có
        chapter_title_selectors = [
            "h2.text-center", 
            "h2.chapter-title", 
            "h2"
        ]
        
        chapter_title_element = None
        for selector in chapter_title_selectors:
            chapter_title_element = soup.select_one(selector)
            if chapter_title_element and chapter_title_element.text.strip():
                break
        
        # Tìm tiêu đề truyện nếu chưa có
        if not title_element:
            # Tìm trong các meta tags
            meta_title = soup.select_one("meta[property='og:title']")
            if meta_title:
                story_title = meta_title.get("content", "Unknown Title")
            else:
                story_title = "Unknown Title"
        else:
            story_title = title_element.text.strip()
        
        chapter_title = chapter_title_element.text.strip() if chapter_title_element else ""
        
        # Kết hợp tiêu đề truyện và tiêu đề chương
        if story_title and chapter_title and story_title != chapter_title:
            title = f"{story_title}\n{chapter_title}"
        else:
            title = story_title
        
        # Tìm phần tử chứa nội dung chính - thử nhiều selector khác nhau
        content_selectors = [
            "div#chapter-content.break-words", 
            "div.break-words#chapter-content",
            "div#chapter-content", 
            "div.chapter-content",
            "div.break-words",
            "article.chapter-c", 
            "div.chapter-c",
            "div.content-chapter", 
            "div.chapter-detail",
            "div.chapter-detail-content",
            "div.chapter",
            "div.content",
            "article.content"
        ]
        
        story_content = None
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element and element.text.strip() and len(element.text.strip()) > 200:
                    story_content = element
                    logger.info(f"Đã tìm thấy nội dung với selector: {selector}")
                    break
            if story_content:
                break
        
        # Nếu vẫn không tìm thấy, thử các phương pháp khác
        if not story_content:
            # Tìm thẻ div lớn sau tiêu đề chương
            if chapter_title_element:
                next_element = chapter_title_element.find_next("div")
                if next_element and len(next_element.text.strip()) > 200:  # Nếu có đủ nội dung
                    story_content = next_element
            
            # Tìm các thẻ div có nhiều nội dung text
            if not story_content:
                divs = soup.find_all("div")
                longest_div = None
                max_length = 200  # Ngưỡng tối thiểu
                
                for div in divs:
                    text = div.get_text(strip=True)
                    if len(text) > max_length and "Copyright" not in text and "facebook" not in text.lower():
                        max_length = len(text)
                        longest_div = div
                
                if longest_div:
                    story_content = longest_div
        
        if not story_content:
            logger.error(f"Không tìm thấy nội dung truyện!")
            return None
        
        # Clone để không làm thay đổi cấu trúc gốc
        content = story_content
        
        # Loại bỏ các phần tử không cần thiết
        for unwanted in content.select("script, style, iframe, canvas, .ads, .comment, .hidden, [id^='middle-content-'], #middle-content-one, #middle-content-two, #middle-content-three"):
            if unwanted:
                try:
                    unwanted.decompose()
                except:
                    pass
        
        # Lấy HTML nội dung để giữ định dạng
        content_html = str(content)
        
        # Chuyển đổi HTML thành văn bản có định dạng, giữ lại các đoạn văn
        # Thay thế các thẻ phổ biến bằng ký tự xuống dòng để giữ định dạng
        text = content_html
        text = re.sub(r'<br\s*/?>', '\n', text)  # Thay thế <br> bằng xuống dòng
        text = re.sub(r'<p.*?>', '\n\n', text)   # Thay thế <p> bằng 2 dòng trống
        text = re.sub(r'</p>', '', text)
        text = re.sub(r'<div.*?>', '\n', text)   # Thay thế <div> bằng xuống dòng
        text = re.sub(r'</div>', '', text)
        text = re.sub(r'<canvas[^>]*>.*?</canvas>', '', text, flags=re.DOTALL)  # Xóa thẻ canvas
        
        # Loại bỏ các thẻ HTML còn lại
        text = re.sub(r'<.*?>', '', text)
        
        # Xóa các dòng trống liên tiếp
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Xóa các nội dung quảng cáo và đoạn text không liên quan
        text = re.sub(r'-----.*?-----', '', text, flags=re.DOTALL)
        text = re.sub(r'Chấm điểm cao nghe nói.*?Không quảng cáo!', '', text, flags=re.DOTALL)
        text = re.sub(r'truyencv\.com|metruyencv\.com', '', text, flags=re.IGNORECASE)
        
        # Xóa khoảng trắng thừa
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()
        
        # Tạo nội dung đầy đủ với tiêu đề
        full_content = f"{title}\n\n{'='*50}\n\n{text}"
        
        # Ghi nội dung vào file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Đã lưu nội dung vào file: {output_file}")
        return output_file
        
    except Exception as e:
        logger.exception(f"Lỗi khi trích xuất nội dung: {str(e)}")
        return None

def extract_all_html_files(input_dir, output_dir=None, combine=False):
    """
    Trích xuất nội dung từ tất cả các file HTML trong thư mục
    
    Args:
        input_dir: Thư mục chứa các file HTML
        output_dir: Thư mục để lưu các file text. Nếu None, sẽ sử dụng input_dir
        combine: Nếu True, sẽ kết hợp tất cả các file thành một file duy nhất
    
    Returns:
        Số lượng file đã xử lý thành công
    """
    try:
        # Nếu không chỉ định output_dir, sử dụng input_dir
        if output_dir is None:
            output_dir = input_dir
        
        # Đảm bảo output_dir tồn tại
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Tìm tất cả các file HTML trong thư mục
        html_files = glob.glob(os.path.join(input_dir, "*.html"))
        html_files.extend(glob.glob(os.path.join(input_dir, "*.htm")))
        
        if not html_files:
            logger.warning(f"Không tìm thấy file HTML nào trong thư mục: {input_dir}")
            return 0
        
        successful = 0
        output_files = []
        
        # Xử lý từng file
        for html_file in html_files:
            # Tạo tên file đầu ra
            base_name = os.path.basename(html_file)
            output_file = os.path.join(output_dir, os.path.splitext(base_name)[0] + ".txt")
            
            # Trích xuất nội dung
            result = extract_story_content(html_file, output_file)
            
            if result:
                successful += 1
                output_files.append(result)
        
        # Kết hợp tất cả file nếu được yêu cầu
        if combine and output_files:
            combined_file = os.path.join(output_dir, "combined_story.txt")
            
            with open(combined_file, 'w', encoding='utf-8') as outfile:
                for output_file in output_files:
                    with open(output_file, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n" + "="*50 + "\n\n")  # Dấu phân cách giữa các chương
            
            logger.info(f"Đã kết hợp {len(output_files)} file vào {combined_file}")
        
        return successful
        
    except Exception as e:
        logger.exception(f"Lỗi khi xử lý các file HTML: {str(e)}")
        return 0 