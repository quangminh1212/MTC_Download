#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script chạy MeTruyenCV Downloader với giao diện đơn giản
"""

import sys
import os
from metruyencv_downloader import MeTruyenCVDownloader
import logging

def print_banner():
    """In banner chương trình"""
    print("=" * 60)
    print("           MeTruyenCV Downloader")
    print("    Tải truyện từ metruyencv.com thành file txt")
    print("=" * 60)

def get_user_input():
    """Lấy input từ người dùng"""
    print("\nNhập thông tin tải truyện:")
    
    # URL truyện
    story_url = input("URL truyện: ").strip()
    if not story_url:
        print("Lỗi: Vui lòng nhập URL truyện!")
        return None
    
    # Chương bắt đầu
    try:
        start_chapter = input("Chương bắt đầu (mặc định 1): ").strip()
        start_chapter = int(start_chapter) if start_chapter else 1
    except ValueError:
        start_chapter = 1
    
    # Chương kết thúc
    try:
        end_chapter = input("Chương kết thúc (Enter để tải hết): ").strip()
        end_chapter = int(end_chapter) if end_chapter else None
    except ValueError:
        end_chapter = None
    
    # Chế độ headless
    headless_input = input("Chạy ẩn browser? (y/n, mặc định y): ").strip().lower()
    headless = headless_input != 'n'
    
    return {
        "url": story_url,
        "start_chapter": start_chapter,
        "end_chapter": end_chapter,
        "headless": headless
    }

def main():
    """Hàm main"""
    print_banner()
    
    # Lấy thông tin từ người dùng
    config = get_user_input()
    if not config:
        return
    
    print(f"\nCấu hình tải:")
    print(f"- URL: {config['url']}")
    print(f"- Chương: {config['start_chapter']} đến {config['end_chapter'] or 'cuối'}")
    print(f"- Chế độ ẩn: {'Có' if config['headless'] else 'Không'}")
    
    confirm = input("\nBắt đầu tải? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Hủy tải.")
        return
    
    # Tạo downloader
    downloader = MeTruyenCVDownloader(headless=config['headless'])
    
    try:
        print("\nBắt đầu tải truyện...")
        downloader.download_story(
            config['url'], 
            start_chapter=config['start_chapter'],
            end_chapter=config['end_chapter']
        )
        print("\nHoàn thành!")
    except KeyboardInterrupt:
        print("\nNgười dùng dừng chương trình")
    except Exception as e:
        print(f"\nLỗi: {e}")
        logging.error(f"Lỗi: {e}")
    finally:
        downloader.close()

if __name__ == "__main__":
    main()
