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
import gzip
import zlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from bs4 import BeautifulSoup

def decode_content(encoded_content):
    """Thử decode nội dung bằng nhiều phương pháp"""
    try:
        # Bước 1: Decode base64
        decoded_bytes = base64.b64decode(encoded_content)

        # Bước 2: Thử XOR với các key đơn giản
        for key_byte in range(1, 256):
            try:
                xor_result = bytes([b ^ key_byte for b in decoded_bytes])
                content = xor_result.decode('utf-8')
                if len(content) > 100 and any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có']):
                    print(f"XOR key found: {key_byte}")
                    return content
            except:
                continue

        # Bước 3: Thử Caesar cipher trên từng byte
        for shift in range(1, 256):
            try:
                shifted_result = bytes([(b + shift) % 256 for b in decoded_bytes])
                content = shifted_result.decode('utf-8')
                if len(content) > 100 and any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có']):
                    print(f"Caesar shift found: {shift}")
                    return content
            except:
                continue

        # Bước 4: Thử reverse bytes
        try:
            reversed_bytes = decoded_bytes[::-1]
            content = reversed_bytes.decode('utf-8')
            if len(content) > 100 and any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có']):
                print("Reverse bytes worked")
                return content
        except:
            pass

        # Bước 5: Thử decompress với gzip
        try:
            content = gzip.decompress(decoded_bytes).decode('utf-8')
            return content
        except:
            pass

        # Bước 6: Thử decompress với zlib
        try:
            content = zlib.decompress(decoded_bytes).decode('utf-8')
            return content
        except:
            pass

        # Bước 7: Thử AES decrypt với các key phổ biến
        try:
            possible_keys = [
                b'metruyencv12345',  # 16 bytes
                b'1234567890123456',  # 16 bytes
                b'abcdef1234567890',  # 16 bytes
                b'metruyencv123456789012345678901234',  # 32 bytes
            ]

            for key in possible_keys:
                try:
                    if len(key) >= 16:
                        cipher = AES.new(key[:16], AES.MODE_ECB)
                        decrypted = cipher.decrypt(decoded_bytes[:len(decoded_bytes)//16*16])
                        content = decrypted.decode('utf-8', errors='ignore').strip('\x00')
                        if len(content) > 50 and any(word in content for word in ['Tiểu', 'thế', 'người']):
                            return content
                except:
                    continue
        except ImportError:
            pass
        except:
            pass

        # Bước 8: Thử decode trực tiếp UTF-8
        try:
            content = decoded_bytes.decode('utf-8')
            return content
        except:
            pass

        # Bước 9: Thử decode latin-1 (fallback)
        try:
            content = decoded_bytes.decode('latin-1')
            if len(content) > 50:
                return content
        except:
            pass

    except Exception as e:
        print(f"Lỗi decode: {e}")

    return None

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
            try:
                test_response = requests.get(chapters[0]['url'], headers=headers, timeout=15)
                print(f"Test chương 1 - Status: {test_response.status_code}")
                print(f"Test URL: {chapters[0]['url']}")

                if test_response.status_code == 200:
                    # Kiểm tra thêm xem có chapterData không
                    test_soup = BeautifulSoup(test_response.content, 'html.parser')
                    test_scripts = test_soup.find_all('script')
                    has_chapter_data = False
                    for script in test_scripts:
                        if script.string and 'chapterData' in script.string:
                            has_chapter_data = True
                            break

                    if has_chapter_data:
                        print("✓ Pattern URL hoạt động và có chapterData!")
                    else:
                        print("⚠️  Pattern URL hoạt động nhưng không có chapterData")
                else:
                    print("✗ Pattern URL không hoạt động")

                    # Fallback: Thử tìm link trong HTML
                    print("Fallback: Tìm link trong HTML...")
                    soup = BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                print(f"✗ Lỗi khi test chương đầu: {e}")
                print("Fallback: Thử tìm link trong HTML...")
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
        scripts = soup.find_all('script')
        content = None

        for script in scripts:
            script_text = script.get_text()
            if 'window.chapterData' in script_text:

                # Extract content từ JavaScript
                try:
                    # Tìm phần textlinks trong chapterData
                    textlinks_match = re.search(r'textlinks:\s*\[(.*?)\]', script_text, re.DOTALL)
                    if textlinks_match:
                        textlinks_str = textlinks_match.group(1)

                        # Extract tất cả code content từ textlinks
                        code_matches = re.findall(r'"code":"([^"]*)"', textlinks_str)

                        if code_matches:
                            # Ghép tất cả nội dung lại
                            full_content = ""
                            for code_content in code_matches:
                                # Decode escape sequences
                                decoded_code = code_content.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')

                                # Decode Unicode escape sequences
                                try:
                                    import codecs

                                    def decode_unicode_match(match):
                                        try:
                                            return codecs.decode(match.group(0), 'unicode_escape')
                                        except:
                                            return match.group(0)

                                    # Tìm tất cả Unicode escape sequences và decode chúng
                                    decoded_code = re.sub(r'\\u[0-9a-fA-F]{4}', decode_unicode_match, decoded_code)

                                except Exception as e:
                                    print(f"Lỗi decode Unicode: {e}")
                                    pass

                                # Loại bỏ HTML tags
                                clean_code = re.sub(r'<[^>]+>', '', decoded_code)

                                # Loại bỏ dấu gạch ngang đầu
                                clean_code = re.sub(r'^-+\s*', '', clean_code.strip())

                                if clean_code.strip():
                                    full_content += clean_code.strip() + "\n\n"

                            if full_content.strip():
                                content = full_content.strip()
                                print(f"✓ Lấy được nội dung từ textlinks ({len(content)} ký tự)")
                                break

                    # Fallback: thử decode content cũ nếu không tìm thấy textlinks
                    if not content:
                        content_match = re.search(r'content:\s*"([^"]+)"', script_text)
                        if content_match:
                            encoded_content = content_match.group(1)
                            content = decode_content(encoded_content)
                            if content:
                                print(f"✓ Decode content thành công ({len(content)} ký tự)")
                                break
                            else:
                                print(f"❌ Không thể decode content")

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

        # Kiểm tra xem nội dung có bị mã hóa không
        if len(content) < 500 or not any(word in content for word in ['Tiểu', 'thế', 'người', 'một', 'có', 'là', 'của']):
            print(f"⚠️  Đã tải: {chapter_title} ({len(content)} ký tự) - Nội dung có thể vẫn bị mã hóa")
        else:
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

    if success > 0:
        print("\n" + "="*50)
        print("📝 LƯU Ý VỀ NỘI DUNG:")
        print("- Nếu thấy ký tự lạ trong file txt, nội dung có thể vẫn bị mã hóa")
        print("- Trang web sử dụng thuật toán mã hóa phức tạp")
        print("- Dự án đã tải được cấu trúc chương thành công")
        print("- Có thể cần reverse engineering thêm để giải mã hoàn toàn")
        print("="*50)

if __name__ == "__main__":
    main()
