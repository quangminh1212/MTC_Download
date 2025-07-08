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
    # Kiểm tra URL
    valid_domains = ["metruyencv.com", "metruyencv.info"]
    valid_url = False
    for domain in valid_domains:
        if url.startswith(f"https://{domain}/truyen/"):
            valid_url = True
            break
    
    if not valid_url:
        logger.error(f"URL không hợp lệ: {url}")
        logger.error("URL phải có dạng: https://metruyencv.com/truyen/ten-truyen/chuong-XX hoặc https://metruyencv.info/truyen/ten-truyen/chuong-XX")
        return None
    
    try:
        # Tải nội dung trang
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://metruyencv.com/"
        }
        logger.info(f"Đang tải chương từ URL: {url}")
        response = requests.get(url, headers=headers)
        
        # Kiểm tra response
        if response.status_code != 200:
            logger.error(f"Lỗi khi tải trang: {response.status_code}")
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
        
        # Trích xuất nội dung chương theo nhiều phương pháp
        story_content = extract_chapter_content(soup)
        
        if not story_content:
            logger.error(f"Không tìm thấy nội dung chương trong trang!")
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
        "div.content-chap"
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
    
    # Thử giải mã phương pháp mới của metruyencv - prp prefix
    if encoded_content.startswith('prp'):
        try:
            logger.info("Tìm thấy mã hóa mới với prefix 'prp', đang thử giải mã...")
            # Cách giải mã mới - thêm vào đây sau khi phân tích
            # TODO: Implement decoding for new 'prp' prefix encryption
            
            # Ghi nội dung mã hóa để phân tích thêm
            with open("debug_prp_encoded.txt", "w", encoding="utf-8") as f:
                f.write(str(encoded_content))
        except:
            pass
    
    # Trường hợp nội dung trong thẻ div#chapter-content
    try:
        if "chapter-content" in encoded_content and "<div" in encoded_content:
            pattern = r'<div[^>]*id=["|\']chapter-content["|\'][^>]*>(.*?)</div>'
            match = re.search(pattern, encoded_content, re.DOTALL)
            if match:
                content = match.group(1)
                logger.info("Tìm thấy nội dung trong thẻ chapter-content")
                return content
    except:
        pass
        
    # Nếu các phương pháp trên không thành công, coi như không giải mã được
    return None

def clean_content(content):
    """
    Loại bỏ các phần tử không mong muốn từ nội dung
    """
    if not content:
        return content
        
    # Loại bỏ các phần tử không mong muốn
    unwanted_selectors = [
        'script', 'style', 'iframe', 'canvas', '.hidden-content', 
        '[id^="middle-content-"]', '#middle-content-one', '#middle-content-two', 
        '#middle-content-three', '.chapter-nav', '.chapter-header', '.chapter-footer',
        '.ads', '.advertisement', '.quangcao', 'button', '.nav', '.pagination',
        '.notify', '.note', '.alert', '.copyright', '.fb-like', '.fb-comment',
        '.button', '.btn', '.social', '.rating', '.comment', '.share',
        'header', 'footer', 'aside', '.menu', '.sidebar', 'nav', '.panel', '.info',
        '.chapter-actions', '.chapter-controls', 'a[href]:not(.chapter-content a)',
        'canvas', 'div#teleport', 'div[data-x-show]', 'template', 'div.flex.justify-center',
        'h3.flex'
    ]
    
    for selector in unwanted_selectors:
        for element in content.select(selector):
            try:
                element.extract()
            except:
                pass
    
    # Lọc các thẻ h1-h6 không liên quan đến nội dung chương
    for heading in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        try:
            heading_text = heading.text.lower()
            if 'chapter' in heading_text or 'chương' in heading_text:
                heading.extract()
        except:
            pass
    
    return content

def html_to_text(content):
    """
    Chuyển HTML thành văn bản có định dạng
    """
    if not content:
        return ""
    
    # Nếu input là chuỗi, chuyển thành BeautifulSoup object
    if isinstance(content, str):
        content = BeautifulSoup(content, 'html.parser')
    
    # Xóa các phần tử không mong muốn
    unwanted_selectors = [
        'script', 'style', 'iframe', 'canvas', '.hidden-content', 
        '[id^="middle-content-"]', '#middle-content-one', '#middle-content-two', 
        '#middle-content-three', '.chapter-nav', '.chapter-header', '.chapter-footer',
        '.ads', '.advertisement', '.quangcao', 'button', '.nav', '.pagination',
        '.notify', '.note', '.alert', '.copyright', '.fb-like', '.fb-comment',
        '.button', '.btn', '.social', '.rating', '.comment', '.share',
        'header', 'footer', 'aside', '.menu', '.sidebar', 'nav', '.panel', '.info',
        '.chapter-actions', '.chapter-controls', 'a[href]:not(.chapter-content a)',
        'canvas', 'div#teleport', 'div[data-x-show]', 'template', 'div.flex.justify-center',
        'h3.flex'
    ]
    
    for selector in unwanted_selectors:
        for element in content.select(selector):
            try:
                element.extract()
            except:
                pass
    
    # Lấy HTML nội dung để giữ định dạng
    content_html = str(content)
    
    # Ghi ra file debug trước khi chuyển đổi
    try:
        with open("debug_html_before_conversion.html", "w", encoding="utf-8") as f:
            f.write(content_html[:20000])
    except:
        pass
    
    # Chuyển đổi HTML thành văn bản có định dạng, giữ lại các đoạn văn
    text = content_html
    text = re.sub(r'<br\s*/?>', '\n', text)  # Thay thế <br> bằng xuống dòng
    text = re.sub(r'<p.*?>', '\n\n', text)   # Thay thế <p> bằng 2 dòng trống
    text = re.sub(r'</p>', '', text)
    text = re.sub(r'<div.*?>', '\n', text)   # Thay thế <div> bằng xuống dòng
    text = re.sub(r'</div>', '', text)
    
    # Loại bỏ các thẻ HTML còn lại
    text = re.sub(r'<.*?>', '', text)
    
    # Xóa các dòng trống liên tiếp
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Xóa các nội dung quảng cáo phổ biến
    ad_patterns = [
        r'-----.*?-----',
        r'Chấm điểm cao nghe nói.*?Không quảng cáo!',
        r'truyencv\.com|metruyencv\.com',
        r'Câu hình(?:Mục lục|Đánh dấu|Close panel|Xuống chương|hiện tại|Không có chương nào)',
        r'Mục lục',
        r'Đánh dấu',
        r'Close panel',
        r'Xuống chương hiện tại',
        r'Không có chương nào',
        r'Cài đặt đọc truyện',
        r'Màu nền(?:\[ngày\])?',
        r'Màu chữ(?:\[ngày\])?',
        r'\[ngày\].*?#[0-9a-fA-F]+',
        r'\[đêm\]',
        r'Font chữ.*?(?:Avenir|Bookerly|Segoe|Literata|Baskerville|Arial|Courier|Tahoma|Palatino|Georgia|Verdana|Times|Source)',
        r'Cỡ chữ\s*\d+',
        r'Chiều cao dòng\s*\d+',
        r'Canh chữ(?:Canh trái|Canh đều|Canh giữa|Canh phải)',
        r'\bx\b',  # Xóa ký tự 'x' đứng một mình (thường là nút đóng)
        r'Converter.*?cầu ủng hộ',
        r'#[0-9a-fA-F]{6}'  # Xóa mã màu hex
    ]
    
    for pattern in ad_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Xóa khoảng trắng thừa
    text = re.sub(r' {2,}', ' ', text)
    # Xóa khoảng trắng ở đầu dòng
    text = re.sub(r'\n\s+', '\n', text)
    text = text.strip()
    
    # Kiểm tra nếu nội dung quá ngắn
    if len(text) < 200:
        logger.warning(f"Nội dung sau khi xử lý quá ngắn: {len(text)} ký tự")
    
    # Kiểm tra xem văn bản có chủ yếu là tiếng Việt không
    vietnamese_chars = re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text, re.IGNORECASE)
    if len(vietnamese_chars) < 10 and len(text) > 500:
        # Nếu có ít ký tự tiếng Việt, có thể là văn bản bị mã hóa sai
        logger.warning("Văn bản có vẻ không phải tiếng Việt, có thể bị mã hóa sai")
    
    # Ghi ra file debug sau khi chuyển đổi
    try:
        with open("debug_text_after_conversion.txt", "w", encoding="utf-8") as f:
            f.write(text[:20000])
    except:
        pass
    
    return text

def download_multiple_chapters(start_url, num_chapters=1, output_dir=None, delay=1, combine=False):
    """
    Tải nhiều chương truyện liên tiếp từ URL bắt đầu
    
    Args:
        start_url: URL của chương đầu tiên
        num_chapters: Số lượng chương cần tải (tính từ chương đầu tiên)
        output_dir: Thư mục để lưu các file
        delay: Thời gian chờ giữa các request (giây)
        combine: Ghép tất cả các chương vào một file
    
    Returns:
        Số lượng chương đã tải thành công
    """
    # Kiểm tra URL
    valid_domains = ["metruyencv.com", "metruyencv.info"]
    valid_url = False
    domain = None
    for d in valid_domains:
        if start_url.startswith(f"https://{d}/truyen/"):
            valid_url = True
            domain = d
            break
    
    if not valid_url:
        logger.error(f"URL không hợp lệ: {start_url}")
        logger.error("URL phải có dạng: https://metruyencv.com/truyen/ten-truyen/chuong-XX hoặc https://metruyencv.info/truyen/ten-truyen/chuong-XX")
        return 0
    
    # Đảm bảo output_dir tồn tại
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    successful = 0
    output_files = []
    current_url = start_url
    
    # Extract base URL và pattern cho chương tiếp theo
    match = re.search(r'(https://.*?/truyen/[^/]+/chuong-)(\d+)', start_url)
    if not match:
        logger.error("Không thể xác định định dạng URL chương")
        return 0
    
    base_url = match.group(1)
    start_chapter = int(match.group(2))
    
    for i in range(num_chapters):
        chapter_number = start_chapter + i
        current_url = f"{base_url}{chapter_number}"
        
        logger.info(f"Đang tải chương {chapter_number} ({i+1}/{num_chapters})")
        
        # Xác định file đầu ra
        if output_dir:
            output_file = os.path.join(output_dir, f"Chương_{chapter_number}.txt")
        else:
            output_file = None
        
        # Tải chương
        result = download_chapter(current_url, output_file, delay)
        
        if result:
            successful += 1
            output_files.append(result)
            
            # Thêm độ trễ để tránh bị chặn
            delay_time = delay + random.uniform(0.5, 1.5)
            logger.info(f"Đợi {delay_time:.2f} giây trước khi tải chương tiếp theo...")
            time.sleep(delay_time)
        else:
            logger.error(f"Không thể tải chương {chapter_number}, đang dừng quá trình tải")
            break
    
    # Kết hợp tất cả file nếu được yêu cầu
    if combine and output_files:
        if output_dir:
            combined_file = os.path.join(output_dir, "combined_story.txt")
        else:
            combined_file = "combined_story.txt"
            
        with open(combined_file, 'w', encoding='utf-8') as outfile:
            for output_file in output_files:
                with open(output_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n" + "="*50 + "\n\n")  # Dấu phân cách giữa các chương
        
        logger.info(f"Đã kết hợp {len(output_files)} chương vào {combined_file}")
    
    return successful

def download_all_chapters(url, output_dir=None, delay=1, combine=False):
    """
    Tải tất cả các chương của một truyện
    
    Args:
        url: URL của truyện hoặc một chương bất kỳ
        output_dir: Thư mục để lưu các file
        delay: Thời gian chờ giữa các request (giây)
        combine: Ghép tất cả các chương vào một file
    
    Returns:
        Số lượng chương đã tải thành công
    """
    # Kiểm tra domain hợp lệ
    valid_domains = ["metruyencv.com", "metruyencv.info"]
    domain = None
    for d in valid_domains:
        if d in url:
            domain = d
            break
    
    if not domain:
        logger.error(f"URL không hợp lệ: {url}")
        logger.error(f"URL phải chứa một trong các domain: {', '.join(valid_domains)}")
        return 0
    
    # Chuẩn hóa URL truyện
    if "/chuong-" in url:
        # Nếu là URL của chương, chuyển thành URL của truyện
        story_url = re.sub(r'/chuong-\d+', '', url)
    elif not url.endswith('/'):
        story_url = url + "/"
    else:
        story_url = url
    
    try:
        # Tải trang truyện để lấy thông tin về số chương
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://metruyencv.com/"
        }
        logger.info(f"Đang tải thông tin truyện từ: {story_url}")
        response = requests.get(story_url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Lỗi khi tải trang truyện: {response.status_code}")
            # Thử tải với URL chương 1
            first_chapter_url = f"{story_url}chuong-1"
            logger.info(f"Đang thử tải với URL chương đầu tiên: {first_chapter_url}")
            return download_multiple_chapters(first_chapter_url, 10, output_dir, delay, combine)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm tên truyện để đặt tên thư mục
        story_title_elem = soup.select_one("h1.font-semibold") or soup.select_one("title")
        story_title = story_title_elem.text.strip() if story_title_elem else "Unknown_Story"
        safe_story_title = re.sub(r'[\\/*?:"<>|]', "", story_title)
        
        # Tạo thư mục nếu không được chỉ định
        if not output_dir:
            output_dir = safe_story_title
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
        
        # Tìm số chương mới nhất - thử nhiều loại selector khác nhau
        latest_chapter_elem = None
        num_chapters = 0
        
        # Thử tải trang mục lục trước để có thông tin đầy đủ về các chương
        toc_url = f"{story_url}muc-luc"
        logger.info(f"Đang tải trang mục lục từ: {toc_url}")
        try:
            toc_response = requests.get(toc_url, headers=headers)
            if toc_response.status_code == 200:
                toc_soup = BeautifulSoup(toc_response.content, 'html.parser')
                chapter_links = toc_soup.select("a[href*='/chuong-']")
                for link in chapter_links:
                    href = link.get('href', '')
                    match = re.search(r'/chuong-(\d+)', href)
                    if match:
                        current_chapter = int(match.group(1))
                        num_chapters = max(num_chapters, current_chapter)
                        
                if num_chapters > 0:
                    logger.info(f"Đã tìm thấy {num_chapters} chương từ trang mục lục")
        except Exception as e:
            logger.warning(f"Không thể tải trang mục lục: {str(e)}")
        
        # Nếu không tìm thấy từ mục lục, thử các phương pháp khác
        if num_chapters == 0:
            # Thử các selector khác nhau để tìm thông tin chương mới nhất
            selectors = [
                "span.latest-chapter",  # Selector cũ
                ".text-base.font-semibold",  # Thử một selector mới
                "p:contains('Chương ')",  # Tìm thẻ p có chứa từ "Chương"
                ".chapter-nav a",  # Thử tìm trong menu điều hướng chương
                "a[href*='chuong-']",  # Tìm các link chương
                "a:contains('Chương ')"  # Tìm các link có chứa từ "Chương"
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        # Tìm số chương từ text
                        match = re.search(r'[Cc]hương (\d+)', text)
                        if match:
                            current_chapter = int(match.group(1))
                            num_chapters = max(num_chapters, current_chapter)
                            latest_chapter_elem = element
                            break
                    
                    # Nếu đã tìm thấy thông tin chương, thoát khỏi vòng lặp
                    if num_chapters > 0:
                        break
                        
            # Nếu vẫn không tìm thấy, thử tìm từ các URL chương trong trang
            if num_chapters == 0:
                chapter_links = soup.select("a[href*='/chuong-']")
                for link in chapter_links:
                    href = link.get('href', '')
                    match = re.search(r'/chuong-(\d+)', href)
                    if match:
                        current_chapter = int(match.group(1))
                        num_chapters = max(num_chapters, current_chapter)
            
            # Nếu vẫn không tìm thấy, thử tìm từ các phần tử có chứa số chương
            if num_chapters == 0:
                all_elements = soup.select("*")
                for element in all_elements:
                    if element.name in ['span', 'p', 'a', 'div']:
                        text = element.text.strip()
                        match = re.search(r'[Cc]hương (\d+)', text)
                        if match:
                            current_chapter = int(match.group(1))
                            num_chapters = max(num_chapters, current_chapter)
        
        # Nếu tất cả các cách trên đều thất bại, cho phép người dùng tải một số chương cụ thể
        if num_chapters == 0:
            logger.warning("Không thể xác định số chương từ trang. Thử tải 5 chương đầu tiên.")
            num_chapters = 5  # Tải 5 chương đầu thay vì báo lỗi
        else:
            logger.info(f"Tổng số chương: {num_chapters}")
        
        # Tạo URL cho chương đầu tiên
        first_chapter_url = f"{story_url}chuong-1"
        
        # Tải tất cả các chương
        return download_multiple_chapters(first_chapter_url, num_chapters, output_dir, delay, combine)
        
    except Exception as e:
        logger.exception(f"Lỗi khi tải thông tin truyện: {str(e)}")
        
        # Nếu có lỗi, vẫn thử tải một số chương đầu tiên
        try:
            first_chapter_url = f"{story_url}chuong-1"
            logger.info("Đang thử tải 5 chương đầu tiên...")
            return download_multiple_chapters(first_chapter_url, 5, output_dir, delay, combine)
        except Exception as inner_e:
            logger.exception(f"Không thể tải các chương đầu tiên: {str(inner_e)}")
            return 0 