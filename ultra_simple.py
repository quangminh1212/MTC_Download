#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader - Phiên bản cực đơn giản
Không cần ChromeDriver, sử dụng requests + BeautifulSoup
"""

import os
import time
import json
import requests
from bs4 import BeautifulSoup

def load_config():
    """Đọc cấu hình từ config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except:
        print("Không tìm thấy config.json!")
        return None

def get_story_info(story_url):
    """Lấy thông tin truyện"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(story_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Lấy tên truyện
        title_element = soup.find('h1')
        story_title = title_element.text.strip() if title_element else "Unknown_Story"
        
        # Tạo thư mục
        safe_title = "".join(c for c in story_title if c.isalnum() or c in (' ', '-', '_')).strip()
        story_folder = safe_title.replace(" ", "_")
        os.makedirs(story_folder, exist_ok=True)
        
        print(f"Tên truyện: {story_title}")
        print(f"Thư mục: {story_folder}")
        
        return story_folder
        
    except Exception as e:
        print(f"Lỗi khi lấy thông tin truyện: {e}")
        return None

def get_chapters(story_url):
    """Lấy danh sách chương"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        print("Đang tải trang truyện...")
        response = requests.get(story_url, headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")

        if response.status_code != 200:
            print(f"Lỗi HTTP: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        # Debug: Lưu HTML để kiểm tra
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("Đã lưu HTML vào debug_page.html để kiểm tra")

        # Thử nhiều cách tìm link chương
        print("Đang tìm link chương...")

        # Cách 1: Tìm theo href chứa '/chuong-'
        chapter_links = soup.find_all('a', href=lambda x: x and '/chuong-' in x)
        print(f"Cách 1 - Tìm thấy {len(chapter_links)} link chứa '/chuong-'")

        # Cách 2: Tìm theo href chứa 'chuong'
        if not chapter_links:
            chapter_links = soup.find_all('a', href=lambda x: x and 'chuong' in x.lower())
            print(f"Cách 2 - Tìm thấy {len(chapter_links)} link chứa 'chuong'")

        # Cách 3: Tìm tất cả link và filter
        if not chapter_links:
            all_links = soup.find_all('a', href=True)
            chapter_links = [link for link in all_links if 'chuong' in link.get('href', '').lower()]
            print(f"Cách 3 - Tìm thấy {len(chapter_links)} link từ tất cả {len(all_links)} link")

        # Debug: In ra một vài link đầu tiên
        if chapter_links:
            print("Một vài link đầu tiên:")
            for i, link in enumerate(chapter_links[:5]):
                href = link.get('href', '')
                text = link.text.strip()
                print(f"  {i+1}. {text} -> {href}")
        else:
            print("Không tìm thấy link chương nào!")
            # In ra một vài link bất kỳ để debug
            all_links = soup.find_all('a', href=True)[:10]
            print("Một vài link bất kỳ trên trang:")
            for i, link in enumerate(all_links):
                href = link.get('href', '')
                text = link.text.strip()[:50]
                print(f"  {i+1}. {text} -> {href}")

        chapters = []
        for link in chapter_links:
            url = link.get('href')
            title = link.text.strip()

            if url and title:
                if not url.startswith('http'):
                    url = 'https://metruyencv.com' + url
                chapters.append({"title": title, "url": url})

        print(f"Tìm thấy {len(chapters)} chương hợp lệ")
        return chapters

    except Exception as e:
        print(f"Lỗi khi lấy danh sách chương: {e}")
        import traceback
        traceback.print_exc()
        return []

def download_chapter(chapter_url, chapter_title, story_folder):
    """Tải một chương"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(chapter_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm nội dung chương
        content_selectors = [
            {'id': 'chapter-content'},
            {'class_': 'chapter-content'},
            {'class_': 'content'},
            {'class_': 'story-content'}
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.find('div', selector)
            if content_element:
                break
        
        if not content_element:
            print(f"Không tìm thấy nội dung: {chapter_title}")
            return False
        
        # Lấy text content
        content = content_element.get_text(separator='\n', strip=True)
        
        if not content:
            print(f"Nội dung trống: {chapter_title}")
            return False
        
        # Tạo tên file an toàn
        safe_title = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.txt"
        filepath = os.path.join(story_folder, filename)
        
        # Lưu file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{chapter_title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(content)
        
        print(f"✓ Đã tải: {chapter_title}")
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi tải {chapter_title}: {e}")
        return False

def main():
    """Hàm chính"""
    print("=== MeTruyenCV Downloader (Ultra Simple) ===")
    
    # Đọc cấu hình
    config = load_config()
    if not config:
        return
    
    story_url = config.get("story_url")
    start_chapter = config.get("start_chapter", 1)
    end_chapter = config.get("end_chapter")
    
    if not story_url:
        print("Không tìm thấy story_url trong config.json!")
        return
    
    print(f"URL: {story_url}")
    print(f"Chương: {start_chapter} đến {end_chapter if end_chapter else 'cuối'}")
    
    # Lấy thông tin truyện
    story_folder = get_story_info(story_url)
    if not story_folder:
        return
    
    # Lấy danh sách chương
    chapters = get_chapters(story_url)
    if not chapters:
        print("Không tìm thấy chương nào!")
        return
    
    # Xác định phạm vi tải
    if end_chapter and end_chapter <= len(chapters):
        chapters_to_download = chapters[start_chapter-1:end_chapter]
    else:
        chapters_to_download = chapters[start_chapter-1:]
    
    print(f"Sẽ tải {len(chapters_to_download)} chương")
    
    # Tải từng chương
    success = 0
    for i, chapter in enumerate(chapters_to_download, 1):
        print(f"[{i}/{len(chapters_to_download)}] Đang tải: {chapter['title']}")
        
        if download_chapter(chapter['url'], chapter['title'], story_folder):
            success += 1
        
        time.sleep(1)  # Nghỉ 1 giây
    
    print(f"\nHoàn thành! Đã tải {success}/{len(chapters_to_download)} chương")
    print(f"Truyện được lưu trong thư mục: {story_folder}")

if __name__ == "__main__":
    main()
