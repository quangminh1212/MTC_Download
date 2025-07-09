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
import base64
import re
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

        # Trang này sử dụng JavaScript để load chương động
        # Thử tạo URL chương từ pattern
        print("Trang web sử dụng JavaScript để load chương động")
        print("Thử tạo danh sách chương từ pattern...")

        # Lấy slug từ URL
        slug = story_url.split('/')[-1]  # tan-the-chi-sieu-thi-he-thong

        chapters = []

        # Thử tạo URL cho 608 chương (số từ HTML)
        for i in range(1, 609):  # 608 chương
            chapter_url = f"https://metruyencv.com/truyen/{slug}/chuong-{i}"
            chapter_title = f"Chương {i}"
            chapters.append({"title": chapter_title, "url": chapter_url})

        print(f"Đã tạo {len(chapters)} chương từ pattern")

        # Test chương đầu tiên để xem có hoạt động không
        if chapters:
            print("Đang test chương đầu tiên...")
            test_response = requests.get(chapters[0]['url'], headers=headers, timeout=10)
            print(f"Test chương 1 - Status: {test_response.status_code}")

            if test_response.status_code == 200:
                print("✓ Pattern URL hoạt động!")
            else:
                print("✗ Pattern URL không hoạt động")

                # Fallback: Thử tìm link trong HTML
                print("Fallback: Tìm link trong HTML...")
                soup = BeautifulSoup(response.content, 'html.parser')

                # Tìm link chương đầu tiên từ nút "Đọc Truyện"
                read_button = soup.find('button', onclick=lambda x: x and 'chuong-1' in x)
                if read_button:
                    onclick = read_button.get('onclick', '')
                    if 'location.href=' in onclick:
                        first_chapter_url = onclick.split("'")[1]
                        print(f"Tìm thấy chương đầu từ nút Đọc: {first_chapter_url}")

                        # Tạo lại danh sách từ URL này
                        base_url = first_chapter_url.rsplit('/chuong-', 1)[0]
                        chapters = []
                        for i in range(1, 609):
                            chapter_url = f"{base_url}/chuong-{i}"
                            chapter_title = f"Chương {i}"
                            chapters.append({"title": chapter_title, "url": chapter_url})

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

        if response.status_code != 200:
            print(f"✗ Lỗi HTTP {response.status_code}: {chapter_title}")
            return False

        soup = BeautifulSoup(response.content, 'html.parser')

        # Tìm nội dung từ JavaScript data
        print("Tìm nội dung từ JavaScript data...")

        # Tìm script chứa window.chapterData
        scripts = soup.find_all('script')
        content = None

        for script in scripts:
            script_text = script.get_text()
            if 'window.chapterData' in script_text and 'content:' in script_text:
                print("Tìm thấy window.chapterData")

                # Extract content từ JavaScript
                try:
                    # Tìm phần content: "..."
                    content_match = re.search(r'content:\s*"([^"]+)"', script_text)
                    if content_match:
                        encoded_content = content_match.group(1)
                        print(f"Tìm thấy nội dung mã hóa ({len(encoded_content)} ký tự)")

                        # Thử nhiều cách decode
                        print(f"Nội dung mã hóa: {encoded_content[:50]}...")

                        # Cách 1: Base64 thông thường
                        try:
                            decoded_bytes = base64.b64decode(encoded_content)
                            content = decoded_bytes.decode('utf-8')
                            print(f"Decode base64 thành công ({len(content)} ký tự)")
                            break
                        except Exception as e1:
                            print(f"Lỗi decode base64: {e1}")

                        # Cách 2: Base64 với padding
                        try:
                            missing_padding = len(encoded_content) % 4
                            if missing_padding:
                                encoded_content += '=' * (4 - missing_padding)
                            decoded_bytes = base64.b64decode(encoded_content)
                            content = decoded_bytes.decode('utf-8')
                            print(f"Decode base64 với padding thành công ({len(content)} ký tự)")
                            break
                        except Exception as e2:
                            print(f"Lỗi decode base64 với padding: {e2}")

                        # Cách 3: Thử decode với latin-1 trước
                        try:
                            decoded_bytes = base64.b64decode(encoded_content)
                            content = decoded_bytes.decode('latin-1')
                            print(f"Decode base64 latin-1 thành công ({len(content)} ký tự)")
                            break
                        except Exception as e3:
                            print(f"Lỗi decode base64 latin-1: {e3}")

                        # Cách 4: Có thể nội dung đã được URL decode
                        try:
                            import urllib.parse
                            url_decoded = urllib.parse.unquote(encoded_content)
                            decoded_bytes = base64.b64decode(url_decoded)
                            content = decoded_bytes.decode('utf-8')
                            print(f"Decode URL + base64 thành công ({len(content)} ký tự)")
                            break
                        except Exception as e4:
                            print(f"Lỗi decode URL + base64: {e4}")

                        # Cách 5: Có thể là plain text
                        try:
                            content = encoded_content
                            print(f"Sử dụng plain text ({len(content)} ký tự)")
                            break
                        except Exception as e5:
                            print(f"Lỗi plain text: {e5}")
                            continue
                except Exception as e:
                    print(f"Lỗi khi extract content: {e}")
                    continue

        if not content:
            print(f"Không tìm thấy nội dung trong JavaScript: {chapter_title}")
            return False

        if len(content) < 50:
            print(f"Nội dung quá ngắn ({len(content)} ký tự): {chapter_title}")
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

        print(f"✓ Đã tải: {chapter_title} ({len(content)} ký tự)")
        return True

    except Exception as e:
        print(f"✗ Lỗi khi tải {chapter_title}: {e}")
        import traceback
        traceback.print_exc()
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
