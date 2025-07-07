#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from bs4 import BeautifulSoup

def extract_story_content(html_file, output_file):
    """
    Trích xuất nội dung truyện từ file HTML và lưu vào file text
    """
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
        print("Không tìm thấy nội dung truyện!")
        return False
    
    # Lấy văn bản từ nội dung
    text = story_content.get_text(separator="\n\n", strip=True)
    
    # Xóa các nội dung quảng cáo (nếu có)
    text = re.sub(r'-----.*?-----', '', text, flags=re.DOTALL)
    
    # Tạo nội dung đầy đủ với tiêu đề
    full_content = f"{title}\n\n{text}"
    
    # Ghi nội dung vào file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"Đã lưu nội dung truyện vào file {output_file}")
    return True

def main():
    # Thông tin file đầu vào và đầu ra
    html_file = "Trinh Quan Hiền Vương - Chương 141.html"
    output_file = "Trinh Quan Hiền Vương - Chương 141.txt"
    
    # Kiểm tra file đầu vào tồn tại
    if not os.path.exists(html_file):
        print(f"File HTML {html_file} không tồn tại!")
        return
    
    # Trích xuất nội dung
    extract_story_content(html_file, output_file)

if __name__ == "__main__":
    main() 