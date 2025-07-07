#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module cung cấp các lệnh dòng lệnh cho ứng dụng
"""

import os
import sys
import argparse
import logging

from mtc_downloader.core.downloader import download_chapter, download_multiple_chapters, download_all_chapters
from mtc_downloader.core.extractor import extract_story_content, extract_all_html_files
from mtc_downloader.web.app import run_app as run_web_app

# Thiết lập logging
logger = logging.getLogger(__name__)

def setup_logging(verbose=False):
    """
    Thiết lập logging
    
    Args:
        verbose: Nếu True, sẽ hiển thị log chi tiết hơn
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def download_cmd():
    """Lệnh tải truyện từ MetruyenCV"""
    parser = argparse.ArgumentParser(description='Tải và lưu truyện từ metruyencv.com')
    parser.add_argument('url', help='URL của chương truyện hoặc truyện')
    parser.add_argument('--output', '-o', help='Thư mục hoặc file đầu ra')
    parser.add_argument('--delay', '-d', type=float, default=2, help='Thời gian chờ giữa các request (giây)')
    parser.add_argument('--combine', '-c', action='store_true', help='Kết hợp tất cả các chương thành một file')
    parser.add_argument('--all', '-a', action='store_true', help='Tải tất cả các chương của truyện')
    parser.add_argument('--num', '-n', type=int, default=1, help='Số lượng chương cần tải (khi không dùng --all)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Hiển thị log chi tiết')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    if args.all:
        print(f"Đang tải tất cả các chương từ: {args.url}")
        num_downloaded = download_all_chapters(args.url, args.output, args.delay, args.combine)
        print(f"Đã tải thành công {num_downloaded} chương.")
    elif args.num > 1:
        print(f"Đang tải {args.num} chương từ: {args.url}")
        num_downloaded = download_multiple_chapters(args.url, args.num, args.output, args.delay, args.combine)
        print(f"Đã tải thành công {num_downloaded} chương.")
    else:
        result = download_chapter(args.url, args.output, args.delay)
        if result:
            print(f"Tải chương thành công! Đã lưu vào: {result}")
        else:
            print("Tải chương thất bại.")
            sys.exit(1)

def extract_cmd():
    """Lệnh trích xuất nội dung từ file HTML"""
    parser = argparse.ArgumentParser(description='Trích xuất nội dung truyện từ file HTML')
    parser.add_argument('-i', '--input', help='Đường dẫn đến file HTML hoặc thư mục chứa file HTML')
    parser.add_argument('-o', '--output', help='Đường dẫn đến file đầu ra hoặc thư mục đầu ra')
    parser.add_argument('-c', '--combine', action='store_true', help='Kết hợp tất cả các file thành một file duy nhất')
    parser.add_argument('--verbose', '-v', action='store_true', help='Hiển thị log chi tiết')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # Nếu không chỉ định input, sử dụng thư mục hiện tại
    if not args.input:
        args.input = os.getcwd()
    
    # Kiểm tra xem input là file hay thư mục
    if os.path.isfile(args.input):
        # Trích xuất từ một file
        result = extract_story_content(args.input, args.output)
        if result:
            print(f"Trích xuất thành công! Đã lưu vào: {result}")
        else:
            print("Trích xuất thất bại!")
            sys.exit(1)
    else:
        # Trích xuất từ thư mục
        num_extracted = extract_all_html_files(args.input, args.output, args.combine)
        print(f"Đã trích xuất thành công {num_extracted} file.")

def web_cmd():
    """Lệnh chạy ứng dụng web"""
    parser = argparse.ArgumentParser(description='Chạy ứng dụng web')
    parser.add_argument('--host', default='localhost', help='Host để chạy ứng dụng')
    parser.add_argument('--port', '-p', type=int, default=3000, help='Cổng để chạy ứng dụng')
    parser.add_argument('--debug', '-d', action='store_true', help='Chạy ứng dụng trong chế độ debug')
    parser.add_argument('--verbose', '-v', action='store_true', help='Hiển thị log chi tiết')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    print(f"Đang chạy ứng dụng web tại http://{args.host}:{args.port}")
    run_web_app(args.host, args.port, args.debug)

def gui_cmd():
    """Lệnh chạy ứng dụng giao diện đồ họa"""
    parser = argparse.ArgumentParser(description='Chạy ứng dụng giao diện đồ họa')
    parser.add_argument('--verbose', '-v', action='store_true', help='Hiển thị log chi tiết')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    try:
        from mtc_downloader.gui.app import run_app as run_gui_app
        print("Đang khởi động ứng dụng giao diện đồ họa...")
        run_gui_app()
    except ImportError:
        print("Không thể khởi động ứng dụng giao diện đồ họa. Có thể tkinter chưa được cài đặt.")
        sys.exit(1)

if __name__ == '__main__':
    # Mặc định chạy lệnh download
    download_cmd() 