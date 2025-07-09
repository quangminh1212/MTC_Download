#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra truy cập chương và lấy chapterData
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

def test_chapter():
    """Test truy cập chương cụ thể"""
    print("=== Test Chapter Access ===")
    
    try:
        # Đọc config
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        story_url = config['download']['story_url']
        
        # Tạo URL chương đầu tiên
        slug = story_url.split('/')[-1]  # tan-the-chi-sieu-thi-he-thong
        chapter_url = f"https://metruyencv.com/truyen/{slug}/chuong-1"
        
        print(f"Story URL: {story_url}")
        print(f"Chapter URL: {chapter_url}")
        
        # Tạo Edge driver
        print("Đang khởi tạo Edge...")
        edge_options = EdgeOptions()
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Edge(options=edge_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✓ Đã khởi tạo Edge")
        
        # Truy cập chương đầu tiên
        print(f"Đang truy cập chương 1: {chapter_url}")
        driver.get(chapter_url)
        time.sleep(5)
        
        # Lấy title
        title = driver.title
        print(f"Title: {title}")
        
        # Lấy HTML
        html = driver.page_source
        print(f"HTML length: {len(html)} characters")
        
        # Lưu HTML để kiểm tra
        with open('chapter_source.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✓ Đã lưu HTML vào chapter_source.html")
        
        # Kiểm tra có chapterData không
        if 'chapterData' in html:
            print("✓ Tìm thấy chapterData trong HTML")
            
            # Tìm và extract chapterData
            scripts = driver.find_elements("tag name", "script")
            for script in scripts:
                try:
                    script_text = driver.execute_script("return arguments[0].innerHTML;", script)
                    if script_text and 'window.chapterData' in script_text:
                        print("✓ Tìm thấy window.chapterData")
                        
                        # Lưu script content
                        with open('chapter_script.js', 'w', encoding='utf-8') as f:
                            f.write(script_text)
                        print("✓ Đã lưu script vào chapter_script.js")
                        
                        # Tìm textlinks
                        textlinks_match = re.search(r'textlinks:\s*\[(.*?)\]', script_text, re.DOTALL)
                        if textlinks_match:
                            print("✓ Tìm thấy textlinks")
                            textlinks_str = textlinks_match.group(1)
                            
                            # Extract code content
                            code_matches = re.findall(r'"code":"([^"]*)"', textlinks_str)
                            print(f"✓ Tìm thấy {len(code_matches)} code entries")
                            
                            if code_matches:
                                # Decode và hiển thị mẫu
                                sample_code = code_matches[0]
                                print(f"Sample code (raw): {sample_code[:100]}...")
                                
                                # Decode escape sequences
                                decoded_code = sample_code.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')
                                
                                # Decode Unicode
                                try:
                                    import codecs
                                    def decode_unicode_match(match):
                                        try:
                                            return codecs.decode(match.group(0), 'unicode_escape')
                                        except:
                                            return match.group(0)
                                    
                                    decoded_code = re.sub(r'\\u[0-9a-fA-F]{4}', decode_unicode_match, decoded_code)
                                except Exception as e:
                                    print(f"Lỗi decode Unicode: {e}")
                                
                                # Loại bỏ HTML tags
                                clean_code = re.sub(r'<[^>]+>', '', decoded_code)
                                clean_code = re.sub(r'^-+\s*', '', clean_code.strip())
                                
                                print(f"Sample decoded content: {clean_code[:200]}...")
                                
                                # Lưu tất cả nội dung
                                full_content = ""
                                for code_content in code_matches:
                                    decoded = code_content.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')
                                    try:
                                        decoded = re.sub(r'\\u[0-9a-fA-F]{4}', decode_unicode_match, decoded)
                                    except:
                                        pass
                                    clean = re.sub(r'<[^>]+>', '', decoded)
                                    clean = re.sub(r'^-+\s*', '', clean.strip())
                                    if clean.strip():
                                        full_content += clean.strip() + "\n\n"
                                
                                with open('chapter_content.txt', 'w', encoding='utf-8') as f:
                                    f.write(full_content)
                                print(f"✓ Đã lưu nội dung vào chapter_content.txt ({len(full_content)} ký tự)")
                        
                        # Tìm content cũ (fallback)
                        content_match = re.search(r'content:\s*"([^"]+)"', script_text)
                        if content_match:
                            print("✓ Tìm thấy content field (encoded)")
                            encoded_content = content_match.group(1)
                            print(f"Encoded content: {encoded_content[:100]}...")
                        
                        break
                        
                except Exception as e:
                    continue
        else:
            print("❌ Không tìm thấy chapterData")
            
        # Kiểm tra có form đăng nhập không
        if 'login' in html.lower() or 'đăng nhập' in html.lower():
            print("✓ Tìm thấy form đăng nhập")
        else:
            print("❌ Không tìm thấy form đăng nhập")
        
        driver.quit()
        print("✓ Test hoàn thành")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chapter()
