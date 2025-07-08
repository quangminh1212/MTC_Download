#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script cho MeTruyenCV Downloader
"""

from app import NovelDownloader
import os

def test_single_chapter():
    """Test tải một chương"""
    downloader = NovelDownloader()
    
    # Test với chương đầu tiên của một truyện
    test_url = "https://metruyencv.com/truyen/ta-co-mot-toa-thanh-pho-ngay-tan-the/chuong-1"
    
    print(f"Đang test tải chương: {test_url}")
    
    result = downloader.download_chapter(test_url)
    
    if result and result['content']:
        print(f"✅ Thành công!")
        print(f"Tiêu đề: {result['title']}")
        print(f"Độ dài nội dung: {len(result['content'])} ký tự")
        print(f"Nội dung preview: {result['content'][:200]}...")
        
        # Lưu file test
        with open('test_chapter.txt', 'w', encoding='utf-8') as f:
            f.write(f"{result['title']}\n")
            f.write("=" * 50 + "\n\n")
            f.write(result['content'])
        
        print("✅ Đã lưu file test_chapter.txt")
    else:
        print("❌ Không thể tải chương")

def test_novel_info():
    """Test lấy thông tin truyện"""
    downloader = NovelDownloader()
    
    test_url = "https://metruyencv.com/truyen/ta-co-mot-toa-thanh-pho-ngay-tan-the"
    
    print(f"Đang test lấy thông tin truyện: {test_url}")
    
    info = downloader.get_novel_info(test_url)
    
    if info:
        print(f"✅ Thành công!")
        print(f"Tên truyện: {info['title']}")
        print(f"Tác giả: {info['author']}")
        print(f"URL: {info['url']}")
    else:
        print("❌ Không thể lấy thông tin truyện")

def test_chapter_list():
    """Test lấy danh sách chương"""
    downloader = NovelDownloader()
    
    test_url = "https://metruyencv.com/truyen/ta-co-mot-toa-thanh-pho-ngay-tan-the"
    
    print(f"Đang test lấy danh sách chương: {test_url}")
    
    chapters = downloader.get_chapter_list(test_url)
    
    if chapters:
        print(f"✅ Thành công!")
        print(f"Tổng số chương: {len(chapters)}")
        print("5 chương đầu:")
        for chapter in chapters[:5]:
            print(f"  - Chương {chapter['number']}: {chapter['title']}")
            print(f"    URL: {chapter['url']}")
    else:
        print("❌ Không thể lấy danh sách chương")

def test_download_novel():
    """Test tải truyện (chỉ 3 chương đầu)"""
    downloader = NovelDownloader()
    
    test_url = "https://metruyencv.com/truyen/ta-co-mot-toa-thanh-pho-ngay-tan-the"
    
    print(f"Đang test tải truyện (3 chương đầu): {test_url}")
    
    result = downloader.download_novel(test_url, start_chapter=1, end_chapter=3)
    
    if result:
        print(f"✅ Thành công!")
        print(f"Tên truyện: {result['novel_info']['title']}")
        print(f"Số chương đã tải: {len(result['chapters'])}")
        print(f"File ZIP: {result['zip_file']}")
        
        for chapter in result['chapters']:
            print(f"  - {chapter['title']}")
    else:
        print("❌ Không thể tải truyện")

if __name__ == "__main__":
    print("🚀 Bắt đầu test MeTruyenCV Downloader")
    print("=" * 50)
    
    # Tạo thư mục downloads nếu chưa có
    os.makedirs('downloads', exist_ok=True)
    
    print("\n1. Test lấy thông tin truyện:")
    test_novel_info()
    
    print("\n2. Test lấy danh sách chương:")
    test_chapter_list()
    
    print("\n3. Test tải một chương:")
    test_single_chapter()
    
    print("\n4. Test tải truyện (3 chương đầu):")
    test_download_novel()
    
    print("\n✅ Hoàn thành test!")
