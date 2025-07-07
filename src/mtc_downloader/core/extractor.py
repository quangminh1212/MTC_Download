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
        
        # Tìm thông tin tiêu đề
        title_element = soup.select_one("h2.text-center.text-gray-600")
        title = title_element.text.strip() if title_element else "Unknown Title"
        
        # Tìm phần tử chứa nội dung chính
        story_content = soup.select_one("div#chapter-content")
        
        if not story_content:
            logger.error("Không tìm thấy nội dung truyện!")
            return None
        
        # Lấy văn bản từ nội dung
        text = story_content.get_text(separator="\n\n", strip=True)
        
        # Xóa các nội dung quảng cáo
        text = re.sub(r'-----.*?-----', '', text, flags=re.DOTALL)
        
        # Tạo nội dung đầy đủ với tiêu đề
        full_content = f"{title}\n\n{text}"
        
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