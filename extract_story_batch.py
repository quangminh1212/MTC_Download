#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import glob
from bs4 import BeautifulSoup

def extract_story_content(html_file, output_file=None):
    """
    Trích xuất nội dung truyện từ file HTML và lưu vào file text
    
    Args:
        html_file: Đường dẫn file HTML đầu vào
        output_file: Đường dẫn file text đầu ra. Nếu None, sẽ tự tạo tên file
    
    Returns:
        Đường dẫn file output hoặc None nếu thất bại
    """
    # Nếu không chỉ định output_file, tự tạo tên file từ html_file
    if output_file is None:
        # Thay đổi phần mở rộng từ .html sang .txt
        output_file = os.path.splitext(html_file)[0] + ".txt"
    
    try:
        # Đọc file HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Phân tích HTML bằng BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tìm thông tin tiêu đề
        title_element = soup.select_one("h2.text-center.text-gray-600")
        if not title_element:
            title_element = soup.select_one("h1") or soup.select_one("title")
        
        title = title_element.text.strip() if title_element else os.path.basename(html_file)
        
        # Tìm phần tử chứa nội dung chính
        story_content = soup.select_one("div#chapter-content")
        
        if not story_content:
            print(f"Không tìm thấy nội dung truyện trong file {html_file}!")
            return None
        
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
        return output_file
        
    except Exception as e:
        print(f"Lỗi khi xử lý file {html_file}: {str(e)}")
        return None

def extract_all_html_files(directory='.', output_dir=None, combine=False):
    """
    Trích xuất nội dung từ tất cả các file HTML trong thư mục
    
    Args:
        directory: Thư mục chứa file HTML
        output_dir: Thư mục đầu ra (nếu None thì sử dụng thư mục hiện tại)
        combine: Nếu True, kết hợp tất cả các file thành một file duy nhất
    
    Returns:
        Số lượng file đã xử lý thành công
    """
    # Tìm tất cả file HTML trong thư mục
    html_files = glob.glob(os.path.join(directory, "*.html"))
    
    if not html_files:
        print(f"Không tìm thấy file HTML nào trong thư mục {directory}")
        return 0
    
    successful = 0
    output_files = []
    
    # Xử lý từng file HTML
    for html_file in sorted(html_files):
        # Xác định file đầu ra
        if output_dir:
            base_name = os.path.basename(html_file)
            output_name = os.path.splitext(base_name)[0] + ".txt"
            output_file = os.path.join(output_dir, output_name)
        else:
            output_file = None  # Để hàm extract_story_content tự xác định
        
        # Trích xuất nội dung
        result = extract_story_content(html_file, output_file)
        if result:
            successful += 1
            output_files.append(result)
    
    # Kết hợp tất cả file nếu được yêu cầu
    if combine and output_files:
        combined_file = os.path.join(output_dir if output_dir else directory, "combined_story.txt")
        with open(combined_file, 'w', encoding='utf-8') as outfile:
            for output_file in output_files:
                with open(output_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n" + "="*50 + "\n\n")  # Dấu phân cách giữa các chương
        
        print(f"Đã kết hợp {len(output_files)} file vào {combined_file}")
    
    return successful

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Trích xuất nội dung truyện từ file HTML')
    parser.add_argument('--input', '-i', help='File HTML hoặc thư mục chứa các file HTML')
    parser.add_argument('--output', '-o', help='File text đầu ra hoặc thư mục chứa các file text')
    parser.add_argument('--combine', '-c', action='store_true', help='Kết hợp tất cả các file thành một file')
    
    args = parser.parse_args()
    
    # Nếu người dùng không chỉ định input, sử dụng thư mục hiện tại
    input_path = args.input if args.input else '.'
    
    if os.path.isdir(input_path):
        # Xử lý toàn bộ thư mục
        num_processed = extract_all_html_files(input_path, args.output, args.combine)
        print(f"Đã xử lý thành công {num_processed} file HTML")
    else:
        # Xử lý một file duy nhất
        result = extract_story_content(input_path, args.output)
        if result:
            print("Xử lý thành công!")
        else:
            print("Xử lý thất bại.")

if __name__ == "__main__":
    main() 