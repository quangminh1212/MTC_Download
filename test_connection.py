#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test kết nối với MeTruyenCV.com
"""

import requests
from bs4 import BeautifulSoup
import time

def test_connection():
    """Test kết nối cơ bản"""
    print("🔍 Đang test kết nối với MeTruyenCV.com...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Test trang chủ
        print("📡 Đang kết nối trang chủ...")
        response = requests.get('https://metruyencv.com/', headers=headers, timeout=10)
        print(f"✅ Trang chủ: {response.status_code}")
        
        # Test trang truyện cụ thể
        test_urls = [
            'https://metruyencv.com/truyen/no-le-bong-toi',
            'https://metruyencv.com/truyen/cuu-vuc-kiem-de'
        ]
        
        for url in test_urls:
            print(f"📡 Đang test: {url}")
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"✅ Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    title = soup.find('h1')
                    if title:
                        print(f"📚 Tên truyện: {title.get_text().strip()}")
                    
                    # Test tải một chương
                    chapter_url = f"{url}/chuong-1"
                    print(f"📖 Đang test chương: {chapter_url}")
                    
                    chapter_response = requests.get(chapter_url, headers=headers, timeout=10)
                    print(f"✅ Chương 1: {chapter_response.status_code}")
                    
                    if chapter_response.status_code == 200:
                        chapter_soup = BeautifulSoup(chapter_response.content, 'html.parser')
                        content_element = chapter_soup.find('div', id='chapter-content')
                        if content_element:
                            content_length = len(content_element.get_text())
                            print(f"📄 Độ dài nội dung: {content_length} ký tự")
                        else:
                            print("❌ Không tìm thấy nội dung chương")
                
                print("-" * 50)
                time.sleep(2)  # Delay giữa các request
                
            except Exception as e:
                print(f"❌ Lỗi khi test {url}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False

def test_novel_detection():
    """Test phát hiện số chương"""
    print("\n🔍 Test phát hiện số chương...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    test_url = 'https://metruyencv.com/truyen/no-le-bong-toi'
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tìm thông tin về số chương
            import re
            latest_chapter = 1
            
            for element in soup.find_all(['span', 'div', 'a']):
                text = element.get_text()
                chapter_match = re.search(r'(?:chương|chapter)\s*(\d+)', text.lower())
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                    if chapter_num > latest_chapter:
                        latest_chapter = chapter_num
            
            print(f"📊 Phát hiện có khoảng {latest_chapter} chương")
            
            # Test tải vài chương đầu
            for i in range(1, min(4, latest_chapter + 1)):
                chapter_url = f"{test_url}/chuong-{i}"
                try:
                    chapter_response = requests.get(chapter_url, headers=headers, timeout=10)
                    if chapter_response.status_code == 200:
                        print(f"✅ Chương {i}: Có thể tải")
                    else:
                        print(f"❌ Chương {i}: Lỗi {chapter_response.status_code}")
                except Exception as e:
                    print(f"❌ Chương {i}: Lỗi {e}")
                
                time.sleep(1)
        
    except Exception as e:
        print(f"❌ Lỗi test phát hiện: {e}")

if __name__ == "__main__":
    print("🚀 Bắt đầu test kết nối MeTruyenCV")
    print("=" * 50)
    
    success = test_connection()
    
    if success:
        test_novel_detection()
        print("\n✅ Test hoàn thành! Ứng dụng có thể kết nối với MeTruyenCV.com")
    else:
        print("\n❌ Không thể kết nối với MeTruyenCV.com")
        print("💡 Có thể do:")
        print("   - Không có kết nối internet")
        print("   - Website đang bảo trì")
        print("   - Bị chặn bởi firewall/antivirus")
    
    print("\n🌐 Ứng dụng chính đang chạy tại: http://localhost:5000")
