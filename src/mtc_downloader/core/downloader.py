#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module chứa các chức năng tải truyện từ metruyencv.com
"""

import os
import re
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import json
import base64
import zlib

# Thiết lập logging
logger = logging.getLogger(__name__)

def download_chapter(url, output_file=None, delay=1):
    """
    Tải một chương truyện từ URL của metruyencv.com và lưu thành file text
    
    Args:
        url: URL của chương truyện (ví dụ: https://metruyencv.com/truyen/ten-truyen/chuong-XX)
        output_file: Đường dẫn file đầu ra để lưu nội dung
        delay: Thời gian chờ giữa các request (giây)
    
    Returns:
        Đường dẫn file output hoặc None nếu thất bại
    """
    # Kiểm tra URL và xử lý các định dạng URL khác nhau
    valid_domains = ["metruyencv.com", "metruyencv.info", "metruyencv.net", "metruyencv.vn"]
    valid_url = False
    domain_used = None
    
    # Hỗ trợ nhiều định dạng URL khác nhau
    url_patterns = [
        r"https?://(?:www\.)?({})/.*/chuong-\d+",  # Định dạng mới
        r"https?://(?:www\.)?({})/.+?/.+?/chuong-\d+",  # Định dạng cũ
        r"https?://(?:www\.)?({})/.+?/.+?/\d+",  # Định dạng thay thế (không có prefix chương)
        r"https?://(?:www\.)?({})/.+?/\d+"  # Định dạng rất ngắn gọn
    ]
    
    for pattern in url_patterns:
        for domain in valid_domains:
            current_pattern = pattern.format(domain)
            if re.match(current_pattern, url):
                valid_url = True
                domain_used = domain
                logger.info(f"URL hợp lệ với domain: {domain}, pattern: {current_pattern}")
                break
        if valid_url:
            break
    
    if not valid_url:
        logger.error(f"URL không hợp lệ: {url}")
        logger.error("URL phải có định dạng hợp lệ, ví dụ: https://metruyencv.com/truyen/ten-truyen/chuong-XX")
        return None
    
    try:
        # Tải nội dung trang
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"https://{domain_used}/",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Sec-Ch-Ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"'
        }
        logger.info(f"Đang tải chương từ URL: {url}")
        
        # Thêm cookie để mô phỏng người dùng thực
        cookies = {
            "cf_clearance": "random_string_here",  # Để bypass Cloudflare nếu có
            "mtcv_uuid": "random_uuid_here",  # Các cookie thường được sử dụng bởi trang web
        }
        
        response = requests.get(url, headers=headers, cookies=cookies)
        
        # In thêm thông tin về response để debug
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Kiểm tra response
        if response.status_code != 200:
            logger.error(f"Lỗi khi tải trang: {response.status_code}")
            
            # Lưu nội dung response để phân tích lỗi
            error_file = "error_response.html"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Đã lưu response lỗi vào file: {error_file}")
            
            return None
        
        # Ghi response HTML để debug
        debug_html_file = "debug_response.html"
        with open(debug_html_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"Đã lưu response HTML vào file: {debug_html_file}")
        
        # Phân tích HTML
        # Đảm bảo encoding đúng để xử lý tiếng Việt
        response.encoding = 'utf-8'  # Luôn sử dụng utf-8 để xử lý tiếng Việt
        
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.info(f"Đã parse HTML thành soup")
        
        # Lưu URL vào soup để extract_advanced_content có thể sử dụng
        soup.url = url
        
        # Trích xuất nội dung chương theo nhiều phương pháp
        story_content = extract_chapter_content(soup)
        
        # Nếu không tìm thấy nội dung, thử các phương pháp bổ sung
        if not story_content:
            logger.warning("Không tìm thấy nội dung chương với các phương pháp thông thường, thử phương pháp nâng cao...")
            
            # Thử gọi API lấy nội dung
            try:
                # Xây dựng API URL từ URL chương
                chapter_match = re.search(r'/truyen/([^/]+)/chuong-(\d+)', url)
                if chapter_match:
                    story_slug = chapter_match.group(1)
                    chapter_number = chapter_match.group(2)
                    
                    # Thử các endpoint API có thể có
                    api_endpoints = [
                        f"https://{domain_used}/api/chapters/{story_slug}/{chapter_number}",
                        f"https://{domain_used}/api/v2/chapters/{story_slug}/{chapter_number}",
                        f"https://{domain_used}/api/stories/{story_slug}/chapters/{chapter_number}",
                        f"https://{domain_used}/api/novels/{story_slug}/chapters/{chapter_number}"
                    ]
                    
                    api_headers = headers.copy()
                    api_headers["Accept"] = "application/json"
                    
                    for api_url in api_endpoints:
                        try:
                            logger.info(f"Thử gọi API: {api_url}")
                            api_response = requests.get(api_url, headers=api_headers, cookies=cookies)
                            
                            # Lưu response API để debug
                            with open(f"api_response_{api_endpoints.index(api_url)}.json", 'w', encoding='utf-8') as f:
                                f.write(api_response.text)
                            
                            if api_response.status_code == 200:
                                try:
                                    api_data = api_response.json()
                                    
                                    # Tìm trường content trong JSON response
                                    if isinstance(api_data, dict):
                                        content_html = None
                                        
                                        if "content" in api_data:
                                            content_html = api_data["content"]
                                        elif "data" in api_data and isinstance(api_data["data"], dict) and "content" in api_data["data"]:
                                            content_html = api_data["data"]["content"]
                                            
                                        if content_html:
                                            logger.info("Tìm thấy nội dung trong API response")
                                            
                                            # Giải mã nội dung nếu cần
                                            decoded_content = try_decode_content(content_html)
                                            
                                            if decoded_content:
                                                logger.info("Giải mã nội dung từ API thành công")
                                                story_content = BeautifulSoup(decoded_content, 'html.parser')
                                                break
                                except:
                                    pass
                        except:
                            continue
            except Exception as e:
                logger.warning(f"Lỗi khi thử gọi API: {str(e)}")
        
        # Nếu vẫn không tìm thấy nội dung, thử đọc từ debug HTML
        if not story_content:
            logger.error(f"Không tìm thấy nội dung chương trong trang!")
            
            # Phân tích trang debug để tìm kiếm pettern mã hóa mới
            try:
                with open(debug_html_file, 'r', encoding='utf-8') as f:
                    debug_html = f.read()
                    
                # Tìm các pattern mã hóa mới
                for prefix in ['comtext', 'mtcontent', 'prp']:
                    pattern = f'{prefix}([^"\'\\s]+)'
                    matches = re.findall(pattern, debug_html)
                    
                    if matches:
                        for match in matches:
                            encoded = f"{prefix}{match}"
                            logger.info(f"Tìm thấy nội dung mã hóa với prefix '{prefix}' trong HTML")
                            
                            # Giải mã và trả về nếu thành công
                            decoded = try_decode_content(encoded)
                            if decoded:
                                logger.info(f"Giải mã thành công nội dung với prefix '{prefix}'")
                                story_content = BeautifulSoup(decoded, 'html.parser')
                                break
            except Exception as e:
                logger.error(f"Lỗi khi phân tích debug HTML: {str(e)}")
            
            if not story_content:
                return None
        
        logger.info(f"Đã tìm thấy nội dung chương - chiều dài: {len(str(story_content))}")    
        
        # Tìm tiêu đề chương và tên truyện
        chapter_title, story_name = extract_title_info(soup)
        logger.info(f"Đã tìm thấy tiêu đề: {story_name} - {chapter_title}")
        
        # Lọc và làm sạch nội dung chương
        content = clean_content(story_content)
        logger.info("Đã làm sạch nội dung")
        
        # Chuyển đổi HTML thành văn bản có định dạng, giữ lại các đoạn văn
        text = html_to_text(content)
        logger.info(f"Đã chuyển HTML thành văn bản - chiều dài: {len(text)}")
        
        # Kiểm tra lại nội dung sau khi xử lý
        if len(text) < 200:
            logger.warning("Nội dung chương quá ngắn sau khi xử lý, có thể đã xảy ra lỗi")
            
            # Lưu nội dung gốc để debug
            with open("debug_raw_content.html", "w", encoding="utf-8") as f:
                f.write(str(story_content))
            logger.info("Đã ghi nội dung HTML gốc vào debug_raw_content.html")
            
            # Thử lấy nội dung trực tiếp từ #chapter-content nếu có
            chapter_content = soup.select_one("#chapter-content")
            if chapter_content:
                logger.info("Thử lấy nội dung từ #chapter-content")
                text = html_to_text(chapter_content)
                logger.info(f"Đã lấy được nội dung từ #chapter-content - chiều dài: {len(text)}")
            
            # Ghi nội dung debug
            with open("debug_content.txt", "w", encoding="utf-8") as f:
                f.write(text)
            logger.info("Đã ghi nội dung debug vào debug_content.txt")
        
        # Tìm phần div.break-words#chapter-content nếu nội dung vẫn quá ngắn
        if len(text) < 200:
            logger.info("Thử phương pháp trích xuất khác...")
            chapter_content_div = soup.select_one("div.break-words#chapter-content")
            if chapter_content_div:
                logger.info("Đã tìm thấy div.break-words#chapter-content")
                text = html_to_text(chapter_content_div)
                logger.info(f"Nội dung mới có chiều dài: {len(text)}")
            
            # Thử cách mới nếu vẫn không tìm thấy
            if len(text) < 200:
                scripts = soup.find_all("script")
                for script in scripts:
                    if script.string and "chapterData" in script.string:
                        logger.info("Tìm thấy script chứa chapterData, thử xử lý...")
                        match = re.search(r'window\.chapterData\s*=\s*(\{.*?\});', script.string, re.DOTALL)
                        if match:
                            with open("debug_chapter_data_script.js", "w", encoding="utf-8") as f:
                                f.write(script.string)
        
        # Tạo nội dung đầy đủ với tiêu đề
        full_content = f"{story_name}\n\n{chapter_title}\n\n{'='*50}\n\n{text}"
        
        # Nếu không chỉ định output_file, tự tạo tên file
        if output_file is None:
            # Tạo tên file từ tiêu đề chương, loại bỏ các ký tự không hợp lệ
            safe_title = re.sub(r'[\\/*?:"<>|]', "", chapter_title)
            output_file = f"{safe_title}.txt"
        
        logger.info(f"Đang lưu nội dung vào file: {output_file}")
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Ghi nội dung vào file với encoding UTF-8 với BOM
        try:
            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write(full_content)
            logger.info(f"Đã lưu nội dung chương vào file: {output_file} - kích thước: {len(full_content)} bytes")
            
            # Kiểm tra xem file đã được tạo thành công chưa
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"File đã được tạo thành công với kích thước: {file_size} bytes")
                
                # Lưu một bản sao với tên khác nếu file quá nhỏ (có thể bị lỗi)
                if file_size < 500:
                    backup_file = f"backup_{output_file}"
                    with open(backup_file, 'w', encoding='utf-8-sig') as f:
                        f.write(full_content)
                    logger.info(f"Đã tạo bản sao tại: {backup_file}")
            else:
                logger.error(f"File không tồn tại sau khi ghi: {output_file}")
                
        except Exception as e:
            logger.error(f"Lỗi khi ghi file {output_file}: {str(e)}")
            return None
        
        return output_file
    
    except Exception as e:
        logger.exception(f"Lỗi khi tải chương: {str(e)}")
        return None

def extract_title_info(soup):
    """
    Trích xuất tiêu đề chương và tên truyện từ soup
    """
    # Tìm tiêu đề chương và tên truyện
    chapter_title = None
    story_title = None
    
    # Thử nhiều selector khác nhau cho tiêu đề chương
    chapter_title_selectors = [
        "h2.text-center.text-gray-600",
        "h1.chapter-title",
        "h2.chapter-title",
        "h2",
        "title"
    ]
    
    for selector in chapter_title_selectors:
        element = soup.select_one(selector)
        if element and element.text.strip():
            chapter_title = element
            logger.info(f"Đã tìm thấy tiêu đề chương với selector: {selector}")
            break
            
    # Thử nhiều selector khác nhau cho tên truyện
    story_title_selectors = [
        "h1.text-lg.text-center a.text-title",
        "h1 a",
        "title"
    ]
    
    for selector in story_title_selectors:
        element = soup.select_one(selector)
        if element and element.text.strip():
            story_title = element
            logger.info(f"Đã tìm thấy tên truyện với selector: {selector}")
            break
    
    # Extract text from elements
    title_text = chapter_title.text.strip() if chapter_title else "Unknown Chapter"
    story_name = story_title.text.strip() if story_title else "Unknown Story"
    
    return title_text, story_name

def extract_chapter_content(soup):
    """
    Trích xuất nội dung chương từ soup sử dụng nhiều phương pháp
    """
    story_content = None
    
    # 0. Thử phương pháp nâng cao trước (mới thêm)
    story_content = extract_advanced_content(soup)
    if story_content:
        logger.info("Đã tìm thấy nội dung với phương pháp nâng cao")
        return story_content
    
    # 1. Tìm thẻ id hoặc class thường chứa nội dung chương
    content_selectors = [
        "div#chapter-content",
        "div.chapter-content", 
        "div#chapter-c", 
        "div.chapter-c",
        "div.break-words",
        "div.chapter",
        "div.content",
        "div.content-body",
        "article#article",
        "article.chapter-c",
        "div.nh-read__content",
        "div.reading-content",
        "div.text-content",
        "div.reader-content",
        "div.content-chap",
        "div.chapter__content",  # Thêm các selector mới
        "div.chapter-detail",
        "div.chapter-detail-content",
        "div#chapter", 
        "div#chapterContent",
        "div.chapterContent",
        "div.chapter-body",
        "div.chapter-text",
        "div#content-container"
    ]
    
    # Thử các selector phổ biến trước
    for selector in content_selectors:
        elements = soup.select(selector)
        for element in elements:
            if element and len(element.text.strip()) > 200:
                story_content = element
                logger.info(f"Đã tìm thấy nội dung chương với selector: {selector}")
                return story_content
    
    # 2. Phương pháp đặc biệt cho metruyencv.com: tìm nội dung JavaScript
    story_content = extract_js_content(soup)
    if story_content:
        return story_content
    
    # 3. Nếu không tìm thấy, tìm div có nhiều văn bản nhất sau tiêu đề
    chapter_title_selectors = [
        "h2.text-center.text-gray-600",
        "h1.chapter-title",
        "h2.chapter-title",
        "h2",
        "div.chapter-header"
    ]

    for selector in chapter_title_selectors:
        chapter_title_element = soup.select_one(selector)
        if chapter_title_element:
            # Tìm phần tử chứa nhiều văn bản nhất sau tiêu đề
            next_element = chapter_title_element.find_next("div")
            if next_element and len(next_element.text.strip()) > 200:
                story_content = next_element
                logger.info(f"Đã tìm thấy nội dung chương sau tiêu đề với selector: {selector}")
                break
    
    # 4. Nếu vẫn không có nội dung, tìm kiếm div có nội dung dài nhất
    if not story_content:
        divs = soup.find_all('div')
        max_text_len = 0
        for div in divs:
            text = div.text.strip()
            if len(text) > max_text_len and len(text) > 500:  # Cần ít nhất 500 ký tự để là nội dung chính
                # Kiểm tra nếu div không chứa các từ khóa không mong muốn
                unwanted = ['header', 'footer', 'menu', 'nav', 'sidebar', 'navbar', 'comment']
                if not any(word in str(div.get('class', [])).lower() for word in unwanted):
                    max_text_len = len(text)
                    story_content = div
        
        if story_content:
            logger.info("Đã tìm thấy div chứa nhiều nội dung nhất")
    
    return story_content

def extract_js_content(soup):
    """
    Trích xuất nội dung chương từ JavaScript
    """
    # Tìm script chứa dữ liệu chương
    scripts = soup.find_all('script')
    
    logger.info(f"Tìm thấy {len(scripts)} thẻ script trong trang")
    
    # Tìm biến chapterData
    for idx, script in enumerate(scripts):
        if not script.string:
            continue
            
        # Ghi script ra file để debug
        if idx < 5:  # Chỉ ghi 5 script đầu tiên để tránh quá nhiều dữ liệu
            try:
                with open(f"debug_script_{idx}.js", "w", encoding="utf-8") as f:
                    f.write(str(script.string))
                logger.info(f"Đã ghi script {idx} vào file debug_script_{idx}.js")
            except:
                pass
                
        # Tìm script có chứa dữ liệu chương
        if "chapterData" in script.string:
            logger.info(f"Tìm thấy script {idx} chứa chapterData")
            
            # Tìm kiếm content bên trong chapterData
            patterns = [
                # Tìm content trong chapterData
                r'chapterData\s*=\s*\{.*?content:\s*[\'"`]([^\'"`]+)[\'"`].*?\}',
                # Tìm đối tượng JavaScript đầy đủ
                r'chapterData\s*=\s*(\{.+?\});',
                # Tìm chỉ thuộc tính content
                r'content:\s*[\'"`]([^\'"`]+)[\'"`]',
                # Tìm thuộc tính content trong format JSON
                r'\"content\":\s*\"([^\"]+)\"',
                # Format JSON với dấu nháy đơn
                r'\'content\':\s*\'([^\']+)\''
            ]
            
            for pattern in patterns:
                try:
                    match = re.search(pattern, script.string, re.DOTALL)
                    if match:
                        content_data = match.group(1)
                        logger.info(f"Tìm thấy dữ liệu với pattern: {pattern[:30]}...")
                        
                        # Trích xuất nội dung và giải mã
                        decoded_content = try_decode_content(content_data)
                        if decoded_content:
                            logger.info(f"Đã giải mã nội dung thành công, độ dài: {len(decoded_content)}")
                            return BeautifulSoup(decoded_content, 'html.parser')
                        else:
                            logger.warning("Không thể giải mã nội dung")
                except Exception as e:
                    logger.warning(f"Lỗi khi trích xuất với pattern: {str(e)}")
    
    # Tìm kiếm trong các biến JavaScript khác
    content_var_names = ["chapterContent", "chapter_content", "content", "_content", "chapter.content"]
    for script in scripts:
        if script.string:
            # Tạo và ghi nội dung script để debug
            try:
                with open("debug_script_content.js", "w", encoding="utf-8") as f:
                    f.write(str(script.string)[:10000])  # Giới hạn kích thước
            except:
                pass
            
            # Tìm các khuôn mẫu phổ biến cho nội dung chương
            for var_name in content_var_names:
                patterns = [
                    rf'var\s+{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                    rf'let\s+{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                    rf'const\s+{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                    rf'{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                    rf'{var_name}:\s*[\'"`]([^\'"`]+)[\'"`]'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        encoded_content = match.group(1)
                        logger.info(f"Tìm thấy biến {var_name} với nội dung mã hóa")
                        decoded_content = try_decode_content(encoded_content)
                        if decoded_content:
                            logger.info(f"Đã giải mã nội dung thành công từ biến {var_name}")
                            return BeautifulSoup(decoded_content, 'html.parser')
    
    # Thử tìm trực tiếp trong chapterData.content
    chapter_data_pattern = r'window\.chapterData\s*=\s*(\{.*?\});'
    for script in scripts:
        if script.string and 'window.chapterData' in script.string:
            match = re.search(chapter_data_pattern, script.string, re.DOTALL)
            if match:
                try:
                    # Thay thế undefined thành null để parse JSON
                    content_json = re.sub(r'undefined', 'null', match.group(1))
                    # Dọn dẹp để có thể parse JSON
                    content_json = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', content_json)
                    # Thay thế các dấu nháy đơn thành nháy kép cho chuỗi
                    content_json = re.sub(r"'([^']*)'", r'"\1"', content_json)
                    
                    import json
                    try:
                        chapter_data = json.loads(content_json)
                        logger.info("Đã parse được chapterData dưới dạng JSON")
                        
                        if 'content' in chapter_data:
                            content_html = chapter_data['content']
                            # Ghi nội dung để debug
                            with open("debug_content.txt", "w", encoding="utf-8") as f:
                                f.write(str(content_html))
                            
                            # Giải mã nội dung
                            decoded_content = try_decode_content(content_html)
                            if decoded_content:
                                return BeautifulSoup(decoded_content, 'html.parser')
                            else:
                                return BeautifulSoup(content_html, 'html.parser')
                    except json.JSONDecodeError as e:
                        logger.warning(f"Lỗi parse JSON: {str(e)}")
                except Exception as e:
                    logger.warning(f"Lỗi khi xử lý chapterData: {str(e)}")
    
    return None

def extract_advanced_content(soup):
    """
    Trích xuất nội dung sử dụng phương pháp nâng cao cho các phiên bản mới của metruyencv
    
    Args:
        soup: BeautifulSoup object của trang
    
    Returns:
        BeautifulSoup object của nội dung hoặc None nếu không tìm thấy
    """
    logger.info("Đang thử phương pháp trích xuất nội dung nâng cao...")
    
    # 1. Tìm kiếm script sử dụng kỹ thuật obfuscation mới
    scripts = soup.find_all('script')
    
    # Tìm kiếm trong script có chứa chapterContent hoặc __NUXT__
    for script in scripts:
        if not script.string:
            continue
            
        script_content = str(script.string)
        
        # Lưu script để phân tích
        with open("advanced_script_analysis.js", "w", encoding="utf-8") as f:
            f.write(script_content[:20000])
        
        # Phương pháp 1: Tìm dữ liệu trong __NUXT__
        if "__NUXT__" in script_content:
            logger.info("Tìm thấy __NUXT__ data trong script")
            
            # Tìm nội dung chương trong __NUXT__ data
            nuxt_pattern = r'__NUXT__\s*=\s*\(function\([^)]*\)\s*\{(.*?)return\s*\{(.*?)\}\s*\}\([^)]*\)\)'
            nuxt_match = re.search(nuxt_pattern, script_content, re.DOTALL)
            
            if nuxt_match:
                nuxt_data = nuxt_match.group(0)
                
                # Tìm state.chapter.content hoặc chapter.content
                content_patterns = [
                    r'state:\s*\{.*?chapter:\s*\{.*?content:\s*[\'"`]([^\'"`]+)[\'"`]',
                    r'chapter:\s*\{.*?content:\s*[\'"`]([^\'"`]+)[\'"`]'
                ]
                
                for pattern in content_patterns:
                    content_match = re.search(pattern, nuxt_data, re.DOTALL)
                    if content_match:
                        encoded_content = content_match.group(1)
                        logger.info("Tìm thấy nội dung chương trong __NUXT__ data")
                        
                        # Giải mã nội dung
                        decoded_content = try_decode_content(encoded_content)
                        if decoded_content:
                            logger.info("Giải mã nội dung trong __NUXT__ data thành công")
                            return BeautifulSoup(decoded_content, 'html.parser')
        
        # Phương pháp 2: Tìm JSON data object
        json_data_pattern = r'({[^{]*?"chapterData"[^{]*?:[^{]*?{.*?}[^}]*?})'
        json_match = re.search(json_data_pattern, script_content, re.DOTALL)
        
        if json_match:
            try:
                json_str = json_match.group(1)
                # Làm sạch chuỗi JSON
                json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)
                json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
                
                # Thử parse JSON
                import json
                try:
                    data = json.loads(json_str)
                    if "chapterData" in data and "content" in data["chapterData"]:
                        encoded_content = data["chapterData"]["content"]
                        logger.info("Tìm thấy nội dung trong JSON data object")
                        
                        # Giải mã nội dung
                        decoded_content = try_decode_content(encoded_content)
                        if decoded_content:
                            logger.info("Giải mã nội dung từ JSON data object thành công")
                            return BeautifulSoup(decoded_content, 'html.parser')
                except json.JSONDecodeError:
                    pass
            except Exception as e:
                logger.debug(f"Lỗi khi xử lý JSON data: {str(e)}")
        
        # Phương pháp 3: Trích xuất từ biến JavaScript lồng nhau
        nested_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'const\s+initialState\s*=\s*({.*?});',
            r'var\s+initialState\s*=\s*({.*?});'
        ]
        
        for pattern in nested_patterns:
            state_match = re.search(pattern, script_content, re.DOTALL)
            if state_match:
                state_data = state_match.group(1)
                # Tìm nội dung chương trong state
                content_match = re.search(r'content:\s*[\'"`]([^\'"`]+)[\'"`]', state_data, re.DOTALL)
                if content_match:
                    encoded_content = content_match.group(1)
                    logger.info("Tìm thấy nội dung chương trong initial state")
                    
                    # Giải mã nội dung
                    decoded_content = try_decode_content(encoded_content)
                    if decoded_content:
                        logger.info("Giải mã nội dung từ initial state thành công")
                        return BeautifulSoup(decoded_content, 'html.parser')
    
    # 2. Tìm kiếm các phần tử script với type=application/json
    json_scripts = soup.find_all("script", attrs={"type": "application/json"})
    for script in json_scripts:
        try:
            if script.string:
                import json
                data = json.loads(script.string)
                # Tìm kiếm thuộc tính có thể chứa nội dung
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict) and "content" in value:
                            encoded_content = value["content"]
                            if isinstance(encoded_content, str) and len(encoded_content) > 100:
                                logger.info(f"Tìm thấy nội dung trong script JSON, khóa: {key}")
                                
                                # Giải mã nội dung
                                decoded_content = try_decode_content(encoded_content)
                                if decoded_content:
                                    logger.info("Giải mã nội dung từ script JSON thành công")
                                    return BeautifulSoup(decoded_content, 'html.parser')
        except Exception as e:
            logger.debug(f"Lỗi khi phân tích script JSON: {str(e)}")
    
    # 3. Tìm kiếm các phần tử div bị ẩn có chứa nội dung
    hidden_divs = soup.find_all("div", attrs={"style": lambda value: value and "display:none" in value})
    hidden_divs.extend(soup.find_all("div", attrs={"class": lambda value: value and "hidden" in value}))
    
    for div in hidden_divs:
        if div and len(div.text) > 500:  # Nội dung chương thường dài
            logger.info("Tìm thấy nội dung trong div ẩn")
            return div
    
    # 4. Tìm trong các thuộc tính data-* của các phần tử
    for elem in soup.find_all(attrs={"data-content": True}):
        encoded_content = elem["data-content"]
        if len(encoded_content) > 100:  # Có vẻ đủ dài để là nội dung chương
            logger.info("Tìm thấy nội dung trong thuộc tính data-content")
            
            # Giải mã nội dung
            decoded_content = try_decode_content(encoded_content)
            if decoded_content:
                logger.info("Giải mã nội dung từ thuộc tính data-content thành công")
                return BeautifulSoup(decoded_content, 'html.parser')
    
    # 5. Tìm kiếm trong các API endpoint từ code JavaScript
    api_patterns = [
        r'(https?://[^"\']+?/api/[^"\']+?/chapters?/[^"\']+?)',
        r'(https?://[^"\']+?/api/[^"\']+?/content[^"\']*?)'
    ]
    
    api_urls = []
    for pattern in api_patterns:
        for script in scripts:
            if script.string:
                matches = re.findall(pattern, script.string)
                api_urls.extend(matches)
    
    if api_urls:
        logger.info(f"Tìm thấy {len(api_urls)} API endpoint tiềm năng, đang thử gọi...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Referer": soup.url if hasattr(soup, 'url') else "https://metruyencv.com/",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        for api_url in api_urls[:3]:  # Chỉ thử 3 URL đầu tiên
            try:
                logger.info(f"Đang gọi API: {api_url}")
                response = requests.get(api_url, headers=headers)
                if response.status_code == 200:
                    try:
                        api_data = response.json()
                        # Tìm trường content trong JSON response
                        if isinstance(api_data, dict):
                            if "content" in api_data:
                                encoded_content = api_data["content"]
                            elif "data" in api_data and isinstance(api_data["data"], dict) and "content" in api_data["data"]:
                                encoded_content = api_data["data"]["content"]
                            else:
                                continue
                                
                            logger.info("Tìm thấy nội dung trong API response")
                            # Giải mã nội dung
                            decoded_content = try_decode_content(encoded_content)
                            if decoded_content:
                                logger.info("Giải mã nội dung từ API thành công")
                                return BeautifulSoup(decoded_content, 'html.parser')
                    except:
                        pass
            except:
                continue
    
    logger.info("Phương pháp trích xuất nâng cao không tìm thấy nội dung")
    return None

def decode_prp_content(encoded_content):
    """
    Giải mã nội dung với prefix 'prp' từ metruyencv.com
    
    Args:
        encoded_content: Chuỗi bắt đầu với 'prp'
        
    Returns:
        Chuỗi HTML đã giải mã hoặc None nếu không thể giải mã
    """
    try:
        if not encoded_content.startswith('prp'):
            return None
            
        logger.info("Đang giải mã nội dung với prefix 'prp'...")
            
        # Bỏ prefix 'prp'
        encoded_content = encoded_content[3:]
        
        # Phân chia thành các khối nhỏ, dấu phân cách là '/'
        chunks = encoded_content.split('/')
        logger.info(f"Phân tách thành {len(chunks)} khối")
        
        decoded_parts = []
        
        for chunk in chunks:
            if not chunk:  # Bỏ qua chunk trống
                continue
                
            # Giải mã từng phần với base64
            try:
                # Thêm padding nếu cần
                padding_needed = len(chunk) % 4
                if padding_needed:
                    chunk += '=' * (4 - padding_needed)
                    
                # Giải mã base64
                decoded_bytes = base64.b64decode(chunk)
                decoded_text = decoded_bytes.decode('utf-8')
                decoded_parts.append(decoded_text)
            except Exception as e:
                logger.debug(f"Không thể giải mã khối '{chunk[:20]}...': {str(e)}")
        
        # Kết hợp tất cả các phần đã giải mã
        result = ''.join(decoded_parts)
        
        # Ghi kết quả để debug
        with open("debug_prp_decoded.txt", "w", encoding="utf-8") as f:
            f.write(result)
        
        if '<' in result and '>' in result:
            logger.info("Đã giải mã thành công nội dung 'prp'!")
            return result
        else:
            # Thử các biến thể khác
            logger.info("Giải mã chưa hoàn toàn, thử các phương pháp bổ sung...")
            return try_decode_content(result)
            
    except Exception as e:
        logger.error(f"Lỗi khi giải mã nội dung 'prp': {str(e)}")
        return None

def try_decode_content(encoded_content):
    """
    Thử nhiều phương pháp khác nhau để giải mã nội dung
    
    Args:
        encoded_content: Chuỗi nội dung đã mã hóa
        
    Returns:
        Chuỗi HTML đã giải mã hoặc None nếu không thể giải mã
    """
    # Kiểm tra nếu nội dung trống
    if not encoded_content:
        return None
    
    # Ghi nội dung mã hóa để debug
    try:
        with open("debug_encoded_content.txt", "w", encoding="utf-8") as f:
            f.write(str(encoded_content[:5000]))  # Giới hạn để tránh file quá lớn
        logger.info("Đã ghi nội dung mã hóa vào debug_encoded_content.txt")
    except:
        pass
    
    # Kiểm tra nếu là nội dung mã hóa với prefix 'prp'
    if isinstance(encoded_content, str) and encoded_content.startswith('prp'):
        decoded = decode_prp_content(encoded_content)
        if decoded:
            return decoded
    
    # Phương pháp mới: Giải mã với prefix "comtext"
    if isinstance(encoded_content, str) and encoded_content.startswith('comtext'):
        logger.info("Phát hiện mã hóa với prefix 'comtext', đang thử giải mã...")
        try:
            # Bỏ prefix 'comtext'
            encoded_part = encoded_content[7:]
            
            # Xử lý encoding mới
            # Thường sau prefix có một mảng base64 được phân tách bởi dấu phẩy
            parts = encoded_part.split(',')
            
            decoded_parts = []
            for part in parts:
                if part:  # Bỏ qua các phần trống
                    try:
                        # Thêm padding nếu cần
                        padding_needed = len(part) % 4
                        if padding_needed:
                            part += '=' * (4 - padding_needed)
                            
                        # Giải mã base64
                        decoded_bytes = base64.b64decode(part)
                        decoded_text = decoded_bytes.decode('utf-8')
                        decoded_parts.append(decoded_text)
                    except:
                        # Nếu phần này không phải base64, giữ nguyên
                        decoded_parts.append(part)
            
            result = ''.join(decoded_parts)
            
            # Ghi kết quả để debug
            with open("debug_comtext_decoded.txt", "w", encoding="utf-8") as f:
                f.write(result)
            
            if '<' in result and '>' in result:
                logger.info("Đã giải mã thành công nội dung 'comtext'!")
                return result
        except Exception as e:
            logger.error(f"Lỗi khi giải mã nội dung 'comtext': {str(e)}")
    
    # Phương pháp mới: Giải mã với prefix "mtcontent"
    if isinstance(encoded_content, str) and encoded_content.startswith('mtcontent'):
        logger.info("Phát hiện mã hóa với prefix 'mtcontent', đang thử giải mã...")
        try:
            # Bỏ prefix 'mtcontent'
            encoded_part = encoded_content[9:]
            
            # Phương pháp giải mã cho mtcontent
            # Thường sử dụng một thuật toán thay thế kí tự đặc biệt
            # Cần kiểm tra dữ liệu thực tế để xác định thuật toán chính xác
            
            # Thử một số thuật toán giải mã tiềm năng
            # 1. Giải mã base64 trực tiếp
            try:
                # Thêm padding nếu cần
                padding_needed = len(encoded_part) % 4
                if padding_needed:
                    encoded_part += '=' * (4 - padding_needed)
                    
                decoded = base64.b64decode(encoded_part).decode('utf-8')
                if '<' in decoded and '>' in decoded:
                    logger.info("Đã giải mã mtcontent bằng base64 tiêu chuẩn!")
                    return decoded
            except:
                pass
            
            # 2. Giải mã với bảng chuyển đổi đặc biệt
            # Đây là một bảng chuyển đổi giả định - cần điều chỉnh theo cách mã hóa thực tế
            mtc_translation_table = str.maketrans({
                'a': 'k', 'b': 'l', 'c': 'm', 'd': 'n', 'e': 'o',
                'f': 'p', 'g': 'q', 'h': 'r', 'i': 's', 'j': 't',
                'k': 'u', 'l': 'v', 'm': 'w', 'n': 'x', 'o': 'y',
                'p': 'z', 'q': 'a', 'r': 'b', 's': 'c', 't': 'd',
                'u': 'e', 'v': 'f', 'w': 'g', 'x': 'h', 'y': 'i',
                'z': 'j', 'A': 'K', 'B': 'L', 'C': 'M', 'D': 'N',
                'E': 'O', 'F': 'P', 'G': 'Q', 'H': 'R', 'I': 'S',
                'J': 'T', 'K': 'U', 'L': 'V', 'M': 'W', 'N': 'X',
                'O': 'Y', 'P': 'Z', 'Q': 'A', 'R': 'B', 'S': 'C',
                'T': 'D', 'U': 'E', 'V': 'F', 'W': 'G', 'X': 'H',
                'Y': 'I', 'Z': 'J'
            })
            
            translated = encoded_part.translate(mtc_translation_table)
            
            try:
                # Thêm padding nếu cần
                padding_needed = len(translated) % 4
                if padding_needed:
                    translated += '=' * (4 - padding_needed)
                    
                decoded = base64.b64decode(translated).decode('utf-8')
                if '<' in decoded and '>' in decoded:
                    logger.info("Đã giải mã mtcontent bằng bảng chuyển đổi và base64!")
                    return decoded
            except:
                pass
            
            # 3. Giải mã với nhiều lớp mã hóa
            # Đôi khi nội dung được mã hóa nhiều lớp base64 lồng nhau
            try:
                current_content = encoded_part
                for _ in range(3):  # Thử giải mã tối đa 3 lớp
                    try:
                        # Thêm padding nếu cần
                        padding_needed = len(current_content) % 4
                        if padding_needed:
                            current_content += '=' * (4 - padding_needed)
                            
                        decoded = base64.b64decode(current_content).decode('utf-8')
                        current_content = decoded
                        
                        if '<' in decoded and '>' in decoded:
                            logger.info(f"Đã giải mã mtcontent sau {_ + 1} lớp base64!")
                            return decoded
                    except:
                        break
            except:
                pass
            
            # Ghi lại encoded_part để phân tích thêm
            with open("mtcontent_encoded.txt", "w", encoding="utf-8") as f:
                f.write(encoded_part)
                
        except Exception as e:
            logger.error(f"Lỗi khi giải mã nội dung 'mtcontent': {str(e)}")
        
    # Cố gắng phân tích xem đây có phải là một JSON được mã hóa không
    try:
        if encoded_content.startswith('{') and encoded_content.endswith('}'):
            import json
            json_data = json.loads(encoded_content)
            if 'content' in json_data and json_data['content']:
                logger.info("Đã tìm thấy nội dung trong JSON")
                return try_decode_content(json_data['content'])
    except:
        pass
    
    # Thử decode base64 trước
    try:
        # Thêm padding nếu cần
        padding = 4 - len(encoded_content) % 4
        if padding < 4:
            padded_content = encoded_content + '=' * padding
        else:
            padded_content = encoded_content
            
        decoded = base64.b64decode(padded_content).decode('utf-8')
        if '<' in decoded and '>' in decoded:  # Có vẻ là HTML
            logger.info("Đã giải mã nội dung base64 thành công")
            return decoded
    except Exception as e:
        logger.debug(f"Lỗi khi giải mã base64 tiêu chuẩn: {str(e)}")
    
    # Thử decode unicode escape
    try:
        decoded = bytes(encoded_content, 'utf-8').decode('unicode_escape')
        if '<' in decoded and '>' in decoded:  # Có vẻ là HTML
            logger.info("Đã giải mã unicode escape thành công")
            return decoded
    except Exception as e:
        logger.debug(f"Lỗi khi giải mã unicode escape: {str(e)}")

    # Thử các phương pháp thay thế cụ thể cho metruyencv
    try:
        # MTC sử dụng nhiều bảng thay thế khác nhau tùy theo phiên bản
        # Đây là các bảng thay thế phổ biến cho metruyencv
        custom_base64_tables = [
            # Bảng thay thế phổ biến nhất
            {
                'L': 'a', 'P': 'b', 'H': 'c', 'S': 'd', 'A': 'e', 
                'I': 'f', 'q': 'g', 'e': 'h', '1': 'i', 'W': 'j',
                'U': 'k', 'Y': 'l', 'R': 'm', '2': 'n', 'm': 'o',
                'N': 'p', 'Z': 'q', 'k': 'r', 'y': 's', 'x': 't',
                'j': 'u', 'w': 'v', 'v': 'w', 'E': 'x', 'K': 'y',
                'f': 'z', 'Q': 'A', 'g': 'B', 'D': 'C', 'X': 'D',
                'p': 'E', 'a': 'F', 'C': 'G', 'V': 'H', '7': 'I',
                't': 'J', '3': 'K', 'c': 'L', 'O': 'M', 'M': 'N',
                '4': 'O', 'G': 'P', '9': 'Q', 'n': 'R', 's': 'S',
                'r': 'T', 'u': 'U', 'z': 'V', 'J': 'W', 'F': 'X',
                'B': 'Y', 'h': 'Z', 'd': '0', 'o': '1', '8': '2',
                'i': '3', '6': '4', 'T': '5', 'b': '6', '5': '7',
                'l': '8', '0': '9', '+': '+', '/': '/'
            },
            # Bảng thay thế thứ hai
            {
                'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 
                'f': 'F', 'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J',
                'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N', 'o': 'O',
                'p': 'P', 'q': 'Q', 'r': 'R', 's': 'S', 't': 'T',
                'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X', 'y': 'Y',
                'z': 'Z', 'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd',
                'E': 'e', 'F': 'f', 'G': 'g', 'H': 'h', 'I': 'i',
                'J': 'j', 'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n',
                'O': 'o', 'P': 'p', 'Q': 'q', 'R': 'r', 'S': 's',
                'T': 't', 'U': 'u', 'V': 'v', 'W': 'w', 'X': 'x',
                'Y': 'y', 'Z': 'z', '0': '0', '1': '1', '2': '2',
                '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
                '8': '8', '9': '9', '+': '+', '/': '/'
            },
            # Bảng thay thế thứ ba (cập nhật mới)
            {
                'p': 'a', 'r': 'b', 's': 'c', 't': 'd', 'u': 'e',
                'v': 'f', 'w': 'g', 'x': 'h', 'y': 'i', 'z': 'j',
                'a': 'k', 'b': 'l', 'c': 'm', 'd': 'n', 'e': 'o',
                'f': 'p', 'g': 'q', 'h': 'r', 'i': 's', 'j': 't',
                'k': 'u', 'l': 'v', 'm': 'w', 'n': 'x', 'o': 'y',
                'q': 'z', 'P': 'A', 'R': 'B', 'S': 'C', 'T': 'D',
                'U': 'E', 'V': 'F', 'W': 'G', 'X': 'H', 'Y': 'I',
                'Z': 'J', 'A': 'K', 'B': 'L', 'C': 'M', 'D': 'N',
                'E': 'O', 'F': 'P', 'G': 'Q', 'H': 'R', 'I': 'S',
                'J': 'T', 'K': 'U', 'L': 'V', 'M': 'W', 'N': 'X',
                'O': 'Y', 'Q': 'Z', '0': '0', '1': '1', '2': '2',
                '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
                '8': '8', '9': '9', '+': '+', '/': '/'
            },
            # Bảng thay thế thứ tư (phiên bản mới nhất)
            {
                'q': 'a', 'w': 'b', 'e': 'c', 'r': 'd', 't': 'e',
                'y': 'f', 'u': 'g', 'i': 'h', 'o': 'i', 'p': 'j',
                'a': 'k', 's': 'l', 'd': 'm', 'f': 'n', 'g': 'o',
                'h': 'p', 'j': 'q', 'k': 'r', 'l': 's', 'z': 't',
                'x': 'u', 'c': 'v', 'v': 'w', 'b': 'x', 'n': 'y',
                'm': 'z', 'Q': 'A', 'W': 'B', 'E': 'C', 'R': 'D',
                'T': 'E', 'Y': 'F', 'U': 'G', 'I': 'H', 'O': 'I',
                'P': 'J', 'A': 'K', 'S': 'L', 'D': 'M', 'F': 'N',
                'G': 'O', 'H': 'P', 'J': 'Q', 'K': 'R', 'L': 'S',
                'Z': 'T', 'X': 'U', 'C': 'V', 'V': 'W', 'B': 'X',
                'N': 'Y', 'M': 'Z', '1': '0', '2': '1', '3': '2',
                '4': '3', '5': '4', '6': '5', '7': '6', '8': '7',
                '9': '8', '0': '9', '+': '+', '/': '/'
            }
        ]
        
        # Thử tất cả các bảng thay thế
        for table_idx, table in enumerate(custom_base64_tables):
            # Áp dụng bảng thay thế
            standard_base64 = ''
            for char in encoded_content:
                standard_base64 += table.get(char, char)
            
            # Thêm padding nếu cần
            padding = 4 - len(standard_base64) % 4
            if padding < 4:
                standard_base64 += '=' * padding
            
            try:
                decoded = base64.b64decode(standard_base64).decode('utf-8')
                if '<' in decoded and '>' in decoded:
                    logger.info(f"Đã giải mã nội dung sử dụng bảng thay thế {table_idx+1} thành công")
                    
                    # Ghi nội dung giải mã để debug
                    with open(f"debug_decoded_content_{table_idx+1}.txt", "w", encoding="utf-8") as f:
                        f.write(decoded[:10000])  # Giới hạn để tránh file quá lớn
                    
                    return decoded
                # Đôi khi nội dung được mã hóa thêm một lần nữa
                if decoded.startswith('eyJ') or decoded.startswith('e1'):  # Đây thường là dấu hiệu của base64 JSON
                    try:
                        double_decoded = base64.b64decode(decoded).decode('utf-8')
                        if '<' in double_decoded and '>' in double_decoded:
                            logger.info(f"Đã giải mã nội dung hai lần với bảng thay thế {table_idx+1} thành công")
                            
                            # Ghi nội dung giải mã để debug
                            with open(f"debug_double_decoded_{table_idx+1}.txt", "w", encoding="utf-8") as f:
                                f.write(double_decoded[:10000])  # Giới hạn để tránh file quá lớn
                            
                            return double_decoded
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Lỗi khi giải mã với bảng thay thế {table_idx+1}: {str(e)}")
                continue
            
    except Exception as e:
        logger.warning(f"Không thể giải mã với phương pháp thay thế: {str(e)}")
    
    # Phương pháp mới: Giải mã content từ cấu trúc dữ liệu đặc biệt
    # Đôi khi nội dung được giấu trong một cấu trúc mảng đặc biệt
    if isinstance(encoded_content, str) and ":" in encoded_content and ";" in encoded_content:
        try:
            # Tách các phần được phân cách bởi dấu chấm phẩy
            parts = encoded_content.split(';')
            decoded_parts = []
            
            for part in parts:
                if ':' in part:
                    # Định dạng thường là "index:value"
                    index_value = part.split(':')
                    if len(index_value) == 2:
                        try:
                            value = index_value[1]
                            # Giải mã value (thường là base64)
                            try:
                                # Thêm padding nếu cần
                                padding_needed = len(value) % 4
                                if padding_needed:
                                    value += '=' * (4 - padding_needed)
                                    
                                decoded = base64.b64decode(value).decode('utf-8')
                                decoded_parts.append(decoded)
                            except:
                                decoded_parts.append(value)
                        except:
                            pass
            
            combined = ''.join(decoded_parts)
            if '<' in combined and '>' in combined:
                logger.info("Đã giải mã nội dung từ cấu trúc dữ liệu đặc biệt")
                return combined
        except:
            pass
    
    # Tìm kiếm nội dung đặc biệt trong chuỗi mã hóa - đôi khi chapterContent ở dạng JSON
    try:
        import re
        import json
        
        # Tìm kiếm mẫu JSON trong chuỗi
        json_patterns = [
            r'\{.*\"content\":\"([^\"]+)\".*\}',
            r'\{.*\'content\':\'([^\']+)\'.*\}'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, encoded_content)
            if match:
                content_str = match.group(1)
                logger.info(f"Tìm thấy content trong JSON pattern: {pattern[:30]}")
                return try_decode_content(content_str)
    except:
        pass
        
    # Phương pháp mới: Giải mã từ chuỗi JS chứa window.chapterData
    if isinstance(encoded_content, str) and 'window.chapterData' in encoded_content:
        try:
            logger.info("Phát hiện định dạng window.chapterData, đang giải mã...")
            
            # Tìm phần content trong chapterData
            content_match = re.search(r'content:\s*[\'"]([^\'"]+)[\'"]', encoded_content)
            if content_match:
                encoded_content_data = content_match.group(1)
                logger.info(f"Tìm thấy nội dung mã hóa trong chapterData: {encoded_content_data[:30]}...")
                
                # Thử giải mã với hàm chuyên biệt
                decoded = decode_chapterdata_content(encoded_content_data)
                if decoded:
                    return decoded
                
                # Nếu không thành công, thử với các phương pháp thông thường
                return try_decode_content(encoded_content_data)
                
        except Exception as e:
            logger.error(f"Lỗi khi xử lý window.chapterData: {str(e)}")

    # Thử nhiều cách giải mã AES
    if len(encoded_content) > 20:  # Chỉ thử với nội dung đủ dài
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            import hashlib
            
            # Một số key phổ biến được sử dụng bởi metruyencv
            common_keys = [
                "metruyencv.com", 
                "metruyencv2022", 
                "mtcv2022",
                "mtcnew2023",
                "mtcv2023",
                "metruyencvpro",
                "mtcshield",
                "mtcprotect"
            ]
            
            # Thử giải mã với các key khác nhau
            for key_text in common_keys:
                try:
                    # Tạo key và IV từ key_text
                    key = hashlib.md5(key_text.encode()).digest()
                    iv = hashlib.sha256(key_text.encode()).digest()[:16]
                    
                    # Giải mã base64 trước
                    try:
                        # Thêm padding nếu cần
                        padding_needed = len(encoded_content) % 4
                        if padding_needed:
                            padded_content = encoded_content + '=' * (4 - padding_needed)
                        else:
                            padded_content = encoded_content
                            
                        encrypted_data = base64.b64decode(padded_content)
                        
                        # Thử các chế độ AES khác nhau
                        for mode in [AES.MODE_CBC, AES.MODE_ECB]:
                            try:
                                if mode == AES.MODE_CBC:
                                    cipher = AES.new(key, AES.MODE_CBC, iv)
                                else:
                                    cipher = AES.new(key, AES.MODE_ECB)
                                
                                decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
                                decoded_text = decrypted.decode('utf-8')
                                
                                if '<' in decoded_text and '>' in decoded_text:
                                    logger.info(f"Giải mã AES thành công với key {key_text}, mode {mode}")
                                    return decoded_text
                            except:
                                continue
                    except:
                        continue
                except:
                    continue
        except ImportError:
            logger.warning("Không có thư viện pycryptodome, bỏ qua giải mã AES")
        except Exception as e:
            logger.debug(f"Lỗi khi thử giải mã AES: {str(e)}")

    # Xử lý dạng đặc biệt: XOR encoding với khóa cố định
    if len(encoded_content) > 20:
        try:
            # Thử giải mã với XOR và khóa thường dùng
            xor_keys = ["mtcv", "metruyencv", "truyen", "chapter", "m3tr4y3n"]
            
            for key in xor_keys:
                try:
                    # Decode base64 trước
                    padding_needed = len(encoded_content) % 4
                    if padding_needed:
                        padded_content = encoded_content + '=' * (4 - padding_needed)
                    else:
                        padded_content = encoded_content
                        
                    data = base64.b64decode(padded_content)
                    
                    # Thực hiện XOR với key
                    key_bytes = key.encode('utf-8')
                    decoded = bytearray()
                    
                    for i in range(len(data)):
                        decoded.append(data[i] ^ key_bytes[i % len(key_bytes)])
                    
                    try:
                        result = decoded.decode('utf-8')
                        if '<' in result and '>' in result:
                            logger.info(f"Giải mã XOR thành công với khóa {key}")
                            return result
                    except:
                        # Thử UTF-16 nếu UTF-8 không hoạt động
                        try:
                            result = decoded.decode('utf-16')
                            if '<' in result and '>' in result:
                                logger.info(f"Giải mã XOR thành công với khóa {key} (UTF-16)")
                                return result
                        except:
                            pass
                except:
                    continue
        except Exception as e:
            logger.debug(f"Lỗi khi thử giải mã XOR: {str(e)}")
            
    # Kiểm tra xem có phải là HTML đã encode
    if '&lt;' in encoded_content and '&gt;' in encoded_content:
        try:
            from html import unescape
            decoded = unescape(encoded_content)
            logger.info("Đã giải mã HTML entities thành công")
            return decoded
        except:
            pass
    
    # Nếu chỉ là HTML thuần túy, trả về nguyên vẹn
    if encoded_content.startswith('<') and '>' in encoded_content:
        logger.info("Nội dung đã là HTML thuần túy")
        return encoded_content
    
    # Phương pháp mới: Giải mã từ chuỗi JS chứa window.chapterData
    if isinstance(encoded_content, str) and 'window.chapterData' in encoded_content:
        try:
            logger.info("Phát hiện định dạng window.chapterData, đang giải mã...")
            
            # Tìm phần content trong chapterData
            content_match = re.search(r'content:\s*[\'"]([^\'"]+)[\'"]', encoded_content)
            if content_match:
                encoded_content_data = content_match.group(1)
                logger.info(f"Tìm thấy nội dung mã hóa trong chapterData: {encoded_content_data[:30]}...")
                
                # Giải mã nội dung
                return try_decode_content(encoded_content_data)
                
        except Exception as e:
            logger.error(f"Lỗi khi giải mã window.chapterData: {str(e)}")

    # Thử nhiều cách giải mã AES
    if len(encoded_content) > 20:  # Chỉ thử với nội dung đủ dài
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            import hashlib
            
            # Một số key phổ biến được sử dụng bởi metruyencv
            common_keys = [
                "metruyencv.com", 
                "metruyencv2022", 
                "mtcv2022",
                "mtcnew2023",
                "mtcv2023",
                "metruyencvpro",
                "mtcshield",
                "mtcprotect"
            ]
            
            # Thử giải mã với các key khác nhau
            for key_text in common_keys:
                try:
                    # Tạo key và IV từ key_text
                    key = hashlib.md5(key_text.encode()).digest()
                    iv = hashlib.sha256(key_text.encode()).digest()[:16]
                    
                    # Giải mã base64 trước
                    try:
                        # Thêm padding nếu cần
                        padding_needed = len(encoded_content) % 4
                        if padding_needed:
                            padded_content = encoded_content + '=' * (4 - padding_needed)
                        else:
                            padded_content = encoded_content
                            
                        encrypted_data = base64.b64decode(padded_content)
                        
                        # Thử các chế độ AES khác nhau
                        for mode in [AES.MODE_CBC, AES.MODE_ECB]:
                            try:
                                if mode == AES.MODE_CBC:
                                    cipher = AES.new(key, AES.MODE_CBC, iv)
                                else:
                                    cipher = AES.new(key, AES.MODE_ECB)
                                
                                decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
                                decoded_text = decrypted.decode('utf-8')
                                
                                if '<' in decoded_text and '>' in decoded_text:
                                    logger.info(f"Giải mã AES thành công với key {key_text}, mode {mode}")
                                    return decoded_text
                            except:
                                continue
                    except:
                        continue
                except:
                    continue
        except ImportError:
            logger.warning("Không có thư viện pycryptodome, bỏ qua giải mã AES")
        except Exception as e:
            logger.debug(f"Lỗi khi thử giải mã AES: {str(e)}")

    # Xử lý dạng đặc biệt: XOR encoding với khóa cố định
    if len(encoded_content) > 20:
        try:
            # Thử giải mã với XOR và khóa thường dùng
            xor_keys = ["mtcv", "metruyencv", "truyen", "chapter", "m3tr4y3n"]
            
            for key in xor_keys:
                try:
                    # Decode base64 trước
                    padding_needed = len(encoded_content) % 4
                    if padding_needed:
                        padded_content = encoded_content + '=' * (4 - padding_needed)
                    else:
                        padded_content = encoded_content
                        
                    data = base64.b64decode(padded_content)
                    
                    # Thực hiện XOR với key
                    key_bytes = key.encode('utf-8')
                    decoded = bytearray()
                    
                    for i in range(len(data)):
                        decoded.append(data[i] ^ key_bytes[i % len(key_bytes)])
                    
                    try:
                        result = decoded.decode('utf-8')
                        if '<' in result and '>' in result:
                            logger.info(f"Giải mã XOR thành công với khóa {key}")
                            return result
                    except:
                        # Thử UTF-16 nếu UTF-8 không hoạt động
                        try:
                            result = decoded.decode('utf-16')
                            if '<' in result and '>' in result:
                                logger.info(f"Giải mã XOR thành công với khóa {key} (UTF-16)")
                                return result
                        except:
                            pass
                except:
                    continue
        except Exception as e:
            logger.debug(f"Lỗi khi thử giải mã XOR: {str(e)}")

def decode_chapterdata_content(encoded_content):
    """
    Giải mã nội dung chapterData từ định dạng được tìm thấy trong script
    
    Args:
        encoded_content: Chuỗi đã mã hóa từ window.chapterData
        
    Returns:
        Chuỗi HTML đã giải mã hoặc None nếu không thể giải mã
    """
    try:
        logger.info("Đang thử giải mã định dạng chapterData đặc biệt...")
        
        # Phương pháp 1: Giải mã trực tiếp với base64 + AES
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            import hashlib
            
            # Thêm padding nếu cần
            padding_needed = len(encoded_content) % 4
            if padding_needed:
                padded_content = encoded_content + '=' * (4 - padding_needed)
            else:
                padded_content = encoded_content
                
            # Giải mã base64
            encrypted_data = base64.b64decode(padded_content)
            
            # Thử các khóa phổ biến
            keys = ["metruyencv2023", "mtcv2023", "mtcsecret", "mtctoken"]
            
            for key_text in keys:
                try:
                    # Tạo key và IV từ key_text
                    key = hashlib.md5(key_text.encode()).digest()
                    iv = key[:16]  # Sử dụng 16 byte đầu của key làm IV
                    
                    # Thử chế độ CBC
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    try:
                        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
                        result = decrypted.decode('utf-8')
                        
                        if '<' in result and '>' in result:
                            logger.info(f"Giải mã chapterData thành công với khóa {key_text}")
                            return result
                    except:
                        pass
                        
                    # Thử chế độ ECB
                    cipher = AES.new(key, AES.MODE_ECB)
                    try:
                        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
                        result = decrypted.decode('utf-8')
                        
                        if '<' in result and '>' in result:
                            logger.info(f"Giải mã chapterData thành công với khóa {key_text} (ECB)")
                            return result
                    except:
                        pass
                except:
                    continue
        except ImportError:
            logger.warning("Không có thư viện pycryptodome, bỏ qua giải mã AES")
        except Exception as e:
            logger.debug(f"Lỗi khi thử giải mã AES cho chapterData: {str(e)}")
        
        # Phương pháp 2: Sử dụng kỹ thuật đặc biệt của metruyencv
        try:
            # Phát hiện mẫu mã hóa đặc biệt trong chapterData
            if '+' in encoded_content and '/' in encoded_content:
                logger.info("Thử giải mã với thuật toán MTC đặc biệt...")
                
                # Thuật toán đặc biệt của MTC: base64 + xor + deflate
                import zlib
                
                # Thêm padding cho base64 nếu cần
                padding_needed = len(encoded_content) % 4
                if padding_needed:
                    padded_content = encoded_content + '=' * (4 - padding_needed)
                else:
                    padded_content = encoded_content
                
                # Giải mã base64
                try:
                    data = base64.b64decode(padded_content)
                    
                    # XOR với các khóa phổ biến
                    xor_keys = ["mtcv", "metruyencv", "truyen", "chapter"]
                    for key in xor_keys:
                        try:
                            key_bytes = key.encode('utf-8')
                            xored_data = bytearray()
                            
                            for i in range(len(data)):
                                xored_data.append(data[i] ^ key_bytes[i % len(key_bytes)])
                            
                            # Thử giải nén với zlib
                            try:
                                decompressed = zlib.decompress(xored_data)
                                result = decompressed.decode('utf-8')
                                
                                if '<' in result and '>' in result:
                                    logger.info(f"Giải mã XOR + zlib thành công với khóa {key}")
                                    return result
                            except:
                                pass
                                
                            # Nếu không giải nén được, thử decode trực tiếp
                            try:
                                result = xored_data.decode('utf-8')
                                if '<' in result and '>' in result:
                                    logger.info(f"Giải mã XOR thành công với khóa {key}")
                                    return result
                            except:
                                pass
                        except:
                            continue
                except:
                    pass
        except Exception as e:
            logger.debug(f"Lỗi khi thử giải mã đặc biệt cho chapterData: {str(e)}")
            
        # Phương pháp 3: Thử decode theo từng chuỗi nhỏ trong chapterData
        try:
            # Tách các phần riêng biệt
            if len(encoded_content) > 20:
                # Chia thành các đoạn có chiều dài bội số của 4
                for chunk_size in [4, 8, 16, 32, 64]:
                    chunks = [encoded_content[i:i+chunk_size] for i in range(0, len(encoded_content), chunk_size)]
                    decoded_chunks = []
                    
                    for chunk in chunks:
                        try:
                            # Thêm padding nếu cần
                            padding_needed = len(chunk) % 4
                            if padding_needed:
                                padded_chunk = chunk + '=' * (4 - padding_needed)
                            else:
                                padded_chunk = chunk
                                
                            # Giải mã base64
                            decoded = base64.b64decode(padded_chunk).decode('utf-8')
                            decoded_chunks.append(decoded)
                        except:
                            decoded_chunks.append(chunk)
                    
                    result = ''.join(decoded_chunks)
                    if '<' in result and '>' in result:
                        logger.info(f"Giải mã theo từng đoạn {chunk_size} thành công")
                        return result
        except Exception as e:
            logger.debug(f"Lỗi khi thử giải mã theo đoạn cho chapterData: {str(e)}")
        
        return None
    except Exception as e:
        logger.error(f"Lỗi khi giải mã chapterData: {str(e)}")
        return None

def download_multiple_chapters(url, num_chapters, output_dir=None, delay=2, combine=False):
    """
    Tải nhiều chương truyện liên tiếp từ một URL bắt đầu
    
    Args:
        url: URL của chương bắt đầu tải
        num_chapters: Số lượng chương cần tải
        output_dir: Thư mục đầu ra để lưu các file
        delay: Thời gian chờ giữa các request (giây)
        combine: Nếu True, kết hợp tất cả các chương vào một file
    
    Returns:
        Số lượng chương tải thành công
    """
    if not url:
        logger.error("URL không được để trống")
        return 0
    
    # Tìm số chương từ URL
    chapter_match = re.search(r'/chuong-(\d+)', url)
    if not chapter_match:
        logger.error(f"Không thể xác định số chương từ URL: {url}")
        return 0
    
    start_chapter = int(chapter_match.group(1))
    logger.info(f"Bắt đầu tải từ chương {start_chapter}")
    
    # Tạo thư mục đầu ra nếu chưa có
    if output_dir is None:
        output_dir = "downloads"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Lưu thông tin URL gốc và truyện
    base_url_match = re.match(r'(.*)/chuong-\d+', url)
    if not base_url_match:
        logger.error(f"URL không hợp lệ: {url}")
        return 0
    
    base_url = base_url_match.group(1)
    logger.info(f"URL cơ sở: {base_url}")
    
    successful_downloads = 0
    output_files = []
    
    for i in range(num_chapters):
        chapter_number = start_chapter + i
        chapter_url = f"{base_url}/chuong-{chapter_number}"
        
        logger.info(f"Đang tải chương {chapter_number} từ URL: {chapter_url}")
        
        # Tạo tên file cho chương
        chapter_file = os.path.join(output_dir, f"chuong-{chapter_number}.txt")
        
        # Tải chương
        result = download_chapter(chapter_url, chapter_file, delay)
        
        if result:
            successful_downloads += 1
            output_files.append(result)
            logger.info(f"Tải chương {chapter_number} thành công!")
        else:
            logger.error(f"Tải chương {chapter_number} thất bại!")
    
    # Nếu yêu cầu kết hợp và có ít nhất 1 chương đã tải thành công
    if combine and successful_downloads > 0:
        combined_file = os.path.join(output_dir, "combined_story.txt")
        logger.info(f"Đang kết hợp {successful_downloads} chương vào file: {combined_file}")
        
        try:
            with open(combined_file, 'w', encoding='utf-8-sig') as outfile:
                # Sắp xếp file theo số chương
                sorted_files = sorted(output_files, key=lambda x: int(re.search(r'chuong-(\d+)', x).group(1)))
                
                for filename in sorted_files:
                    logger.info(f"Đang thêm nội dung từ file: {filename}")
                    
                    with open(filename, 'r', encoding='utf-8-sig') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n" + "="*50 + "\n\n")
            
            logger.info(f"Đã kết hợp tất cả chương vào file: {combined_file}")
        except Exception as e:
            logger.error(f"Lỗi khi kết hợp các chương: {str(e)}")
    
    return successful_downloads

def download_all_chapters(url, output_dir=None, delay=2, combine=False):
    """
    Tải tất cả các chương của một truyện
    
    Args:
        url: URL của truyện hoặc một chương của truyện
        output_dir: Thư mục đầu ra để lưu các file
        delay: Thời gian chờ giữa các request (giây)
        combine: Nếu True, kết hợp tất cả các chương vào một file
    
    Returns:
        Số lượng chương tải thành công
    """
    if not url:
        logger.error("URL không được để trống")
        return 0
    
    # Kiểm tra xem URL là trang truyện hay chương
    is_chapter_url = '/chuong-' in url
    
    # Trích xuất URL truyện
    if is_chapter_url:
        # Nếu là URL của một chương, cần trích xuất URL gốc của truyện
        story_url_match = re.match(r'(.*)/chuong-\d+', url)
        if not story_url_match:
            logger.error(f"Không thể xác định URL truyện từ: {url}")
            return 0
        
        story_url = story_url_match.group(1)
    else:
        # Nếu là URL của truyện, sử dụng trực tiếp
        story_url = url.rstrip('/')
    
    logger.info(f"URL truyện: {story_url}")
    
    # Tạo thư mục đầu ra nếu chưa có
    if output_dir is None:
        output_dir = "downloads"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Lấy thông tin danh sách chương từ trang truyện
    try:
        logger.info(f"Đang tải thông tin truyện từ URL: {story_url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        response = requests.get(story_url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm tất cả các liên kết đến chương
        chapter_links = []
        
        # Tìm thẻ ul.list-chapter có chứa danh sách chương
        chapter_list = soup.select_one("ul.list-chapter")
        
        if chapter_list:
            # Tìm tất cả thẻ li > a trong list-chapter
            for item in chapter_list.select("li > a"):
                href = item.get('href')
                if href and '/chuong-' in href:
                    # Kiểm tra URL chương là tương đối hoặc tuyệt đối
                    if href.startswith('http'):
                        chapter_url = href
                    else:
                        # Nếu là URL tương đối, thêm domain vào
                        domain = re.match(r'(https?://[^/]+)', story_url).group(1)
                        chapter_url = domain + href
                    
                    chapter_links.append(chapter_url)
        
        if not chapter_links:
            # Thử tìm danh sách chương với những selector khác
            # Các trang truyện khác nhau có thể có cấu trúc HTML khác nhau
            alternative_selectors = [
                "div.chapters a",
                "div.chapter-list a",
                "div.list-chapter a",
                "ul#chapterList a",
                "table.table-chapters a"
            ]
            
            for selector in alternative_selectors:
                chapter_elements = soup.select(selector)
                if chapter_elements:
                    for item in chapter_elements:
                        href = item.get('href')
                        if href and '/chuong-' in href:
                            # Kiểm tra URL chương là tương đối hoặc tuyệt đối
                            if href.startswith('http'):
                                chapter_url = href
                            else:
                                # Nếu là URL tương đối, thêm domain vào
                                domain = re.match(r'(https?://[^/]+)', story_url).group(1)
                                chapter_url = domain + href
                            
                            chapter_links.append(chapter_url)
                    if chapter_links:
                        break
        
        if not chapter_links:
            logger.error(f"Không tìm thấy danh sách chương từ URL: {story_url}")
            return 0
        
        # Sắp xếp danh sách chương theo số chương tăng dần
        chapter_links.sort(key=lambda x: int(re.search(r'/chuong-(\d+)', x).group(1)))
        
        logger.info(f"Tìm thấy {len(chapter_links)} chương từ truyện")
        
        # Tải từng chương một
        successful_downloads = 0
        output_files = []
        
        for idx, chapter_url in enumerate(chapter_links):
            chapter_number = idx + 1
            
            logger.info(f"Đang tải chương {chapter_number}/{len(chapter_links)}: {chapter_url}")
            
            # Tạo tên file cho chương
            chapter_file = os.path.join(output_dir, f"chuong-{chapter_number}.txt")
            
            # Tải chương
            result = download_chapter(chapter_url, chapter_file, delay)
            
            if result:
                successful_downloads += 1
                output_files.append(result)
                logger.info(f"Tải chương {chapter_number} thành công!")
            else:
                logger.error(f"Tải chương {chapter_number} thất bại!")
        
        # Nếu yêu cầu kết hợp và có ít nhất 1 chương đã tải thành công
        if combine and successful_downloads > 0:
            combined_file = os.path.join(output_dir, "combined_story.txt")
            logger.info(f"Đang kết hợp {successful_downloads} chương vào file: {combined_file}")
            
            try:
                with open(combined_file, 'w', encoding='utf-8-sig') as outfile:
                    # Sắp xếp file theo số chương
                    sorted_files = sorted(output_files, key=lambda x: int(re.search(r'chuong-(\d+)', x).group(1)))
                    
                    for filename in sorted_files:
                        logger.info(f"Đang thêm nội dung từ file: {filename}")
                        
                        with open(filename, 'r', encoding='utf-8-sig') as infile:
                            outfile.write(infile.read())
                            outfile.write("\n\n" + "="*50 + "\n\n")
                
                logger.info(f"Đã kết hợp tất cả chương vào file: {combined_file}")
            except Exception as e:
                logger.error(f"Lỗi khi kết hợp các chương: {str(e)}")
        
        return successful_downloads
    
    except Exception as e:
        logger.exception(f"Lỗi khi tải danh sách chương: {str(e)}")
        return 0