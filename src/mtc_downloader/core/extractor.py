#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module chứa các chức năng trích xuất nội dung từ file HTML
"""

import os
import re
import glob
from bs4 import BeautifulSoup
import logging
import json
import base64

# Thiết lập logging
logger = logging.getLogger(__name__)

def extract_story_content(html_file, output_file=None):
    """
    Trích xuất nội dung truyện từ file HTML và lưu vào file text
    
    Args:
        html_file: Đường dẫn file HTML đầu vào
        output_file: Đường dẫn file text đầu ra. Nếu None, sẽ tự tạo tên file
    
    Returns:
        Đường dẫn file output hoặc None nếu thất bại
    """
    try:
        # Nếu không chỉ định output_file, tự tạo tên file từ html_file
        if output_file is None:
            # Thay đổi phần mở rộng từ .html sang .txt
            output_file = os.path.splitext(html_file)[0] + ".txt"
        
        # Đọc file HTML
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        # Lưu một bản sao HTML để debug
        debug_file = f"debug_{os.path.basename(html_file)}"
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Đã lưu bản sao HTML để debug: {debug_file}")
        except:
            pass
            
        # Phân tích HTML bằng BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tìm thông tin tiêu đề, lần lượt thử các selector phổ biến
        title_selectors = [
            "h2.text-center.text-gray-600",  # Selector cũ
            "h1.font-semibold",              # Tiêu đề truyện
            "h2",                           # Tiêu đề chương
            "h1",                           # Thử tìm h1 đầu tiên
            "title",                        # Thử tìm trong title
            ".story-title",                 # Class tiêu đề truyện
            ".chapter-title"                # Class tiêu đề chương
        ]
        
        title_element = None
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element and title_element.text.strip():
                break
        
        # Tìm tiêu đề chương (h2) nếu có
        chapter_title_selectors = [
            "h2.text-center", 
            "h2.chapter-title", 
            "h2",
            "h2.text-center.text-gray-600",
            "div.chapter-header"
        ]
        
        chapter_title_element = None
        for selector in chapter_title_selectors:
            chapter_title_element = soup.select_one(selector)
            if chapter_title_element and chapter_title_element.text.strip():
                break
        
        # Tìm tiêu đề truyện nếu chưa có
        story_title_selectors = [
            "h1.text-lg.text-center a.text-title",
            "h1 a.text-title",
            "h1 a"
        ]
        
        story_title = None
        for selector in story_title_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                story_title = element.text.strip()
                logger.info(f"Đã tìm thấy tên truyện với selector: {selector}")
                break
                
        if not story_title:
            # Tìm trong các meta tags
            meta_title = soup.select_one("meta[property='og:title']")
            if meta_title:
                story_title = meta_title.get("content", "Unknown Title")
            else:
                # Tìm từ title trong thẻ head
                title_tag = soup.title
                if title_tag and title_tag.text:
                    # Thường title có dạng "Tên chương - Tên truyện"
                    title_parts = title_tag.text.split('-')
                    if len(title_parts) > 1:
                        story_title = title_parts[-1].strip()
                    else:
                        story_title = title_tag.text.strip()
                else:
                    story_title = "Unknown Title"
        
        chapter_title = chapter_title_element.text.strip() if chapter_title_element else ""
        
        # Kết hợp tiêu đề truyện và tiêu đề chương
        if story_title and chapter_title and story_title != chapter_title:
            title = f"{story_title}\n\n{chapter_title}"
        else:
            title = story_title or chapter_title
        
        # Tìm phần tử chứa nội dung chính - thử nhiều selector khác nhau
        content_selectors = [
            "div#chapter-content.break-words", 
            "div.break-words#chapter-content",
            "div#chapter-content", 
            "div.chapter-content",
            "div.break-words",
            "article.chapter-c", 
            "div.chapter-c",
            "div.content-chapter", 
            "div.chapter-detail",
            "div.chapter-detail-content",
            "div.chapter",
            "div.content",
            "article.content",
            "div#chapter-detail",
            "div.chapter__content",  # Thêm các selector mới
            "div#chapterContent",
            "div.chapterContent",
            "div.chapter-body",
            "div.chapter-text",
            "div#content-container"
        ]
        
        story_content = None
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element and element.text.strip() and len(element.text.strip()) > 200:
                    # Kiểm tra nếu phần tử này không chứa các từ khóa không mong muốn
                    unwanted = ['header', 'footer', 'menu', 'nav', 'sidebar', 'comment']
                    if not any(word in str(element.get('class', [])).lower() for word in unwanted):
                        story_content = element
                        logger.info(f"Đã tìm thấy nội dung với selector: {selector}")
                        break
            if story_content:
                break
        
        # Nếu vẫn không tìm thấy, thử các phương pháp khác
        if not story_content:
            # Kiểm tra mã hóa trong JavaScript
            story_content = extract_from_js(soup)
            
            # Nếu tìm thấy nội dung từ JS, ghi ra file để debug
            if story_content:
                try:
                    with open("debug_js_content.html", "w", encoding="utf-8") as f:
                        f.write(str(story_content))
                    logger.info("Đã ghi nội dung từ JS vào debug_js_content.html")
                except:
                    pass
        
        # Nếu vẫn không tìm thấy, tìm các pattern mã hóa mới
        if not story_content:
            try:
                # Tìm các pattern mã hóa mới trong HTML gốc
                for prefix in ['comtext', 'mtcontent', 'prp']:
                    pattern = f'{prefix}([^"\'\\s]+)'
                    matches = re.findall(pattern, html_content)
                    
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
                logger.warning(f"Lỗi khi tìm pattern mã hóa: {str(e)}")
        
        # Nếu vẫn không tìm thấy, thử tìm trong script với window.__NUXT__ hoặc __INITIAL_STATE__
        if not story_content:
            try:
                scripts = soup.find_all('script')
                for script in scripts:
                    if not script.string:
                        continue
                    
                    script_content = str(script.string)
                    
                    # Tìm trong __NUXT__ data
                    if "__NUXT__" in script_content:
                        logger.info("Tìm thấy __NUXT__ data trong script")
                        
                        # Ghi script để phân tích
                        try:
                            with open("debug_nuxt_script.js", "w", encoding="utf-8") as f:
                                f.write(script_content)
                        except:
                            pass
                        
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
                                        story_content = BeautifulSoup(decoded_content, 'html.parser')
                                        break
                    
                    # Tìm trong __INITIAL_STATE__
                    elif "__INITIAL_STATE__" in script_content:
                        logger.info("Tìm thấy __INITIAL_STATE__ trong script")
                        
                        # Ghi script để phân tích
                        try:
                            with open("debug_initial_state_script.js", "w", encoding="utf-8") as f:
                                f.write(script_content)
                        except:
                            pass
                            
                        # Tìm nội dung trong __INITIAL_STATE__
                        state_pattern = r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});'
                        state_match = re.search(state_pattern, script_content, re.DOTALL)
                        
                        if state_match:
                            state_data = state_match.group(1)
                            # Tìm content trong state
                            content_match = re.search(r'content:\s*[\'"`]([^\'"`]+)[\'"`]', state_data, re.DOTALL)
                            if content_match:
                                encoded_content = content_match.group(1)
                                logger.info("Tìm thấy nội dung trong __INITIAL_STATE__")
                                
                                # Giải mã nội dung
                                decoded_content = try_decode_content(encoded_content)
                                if decoded_content:
                                    logger.info("Giải mã nội dung từ __INITIAL_STATE__ thành công")
                                    story_content = BeautifulSoup(decoded_content, 'html.parser')
                                    break
                                    
            except Exception as e:
                logger.warning(f"Lỗi khi tìm trong script: {str(e)}")
        
        # Nếu vẫn không tìm thấy, tìm div có nhiều nội dung nhất
        if not story_content:
            divs = soup.find_all('div')
            max_text_len = 0
            for div in divs:
                text = div.text.strip()
                if len(text) > max_text_len and len(text) > 500:  # Cần ít nhất 500 ký tự để là nội dung chính
                    # Bỏ qua các div có chứa các từ khóa không phải nội dung chính
                    skip_keywords = ['header', 'footer', 'menu', 'nav', 'sidebar', 'navbar', 'comment']
                    if not any(keyword in str(div.get('class', [])).lower() for keyword in skip_keywords):
                        max_text_len = len(text)
                        story_content = div
            
            if story_content:
                logger.info("Đã tìm thấy nội dung bằng cách tìm div có nhiều văn bản nhất")

        if not story_content:
            logger.error("Không tìm thấy nội dung trong file HTML!")
            return None
            
        # Lấy nội dung đã tìm thấy
        chapter_text = get_clean_text(story_content)
        
        # Kiểm tra xem nội dung có quá ngắn không
        if len(chapter_text) < 200:
            logger.warning("Nội dung trích xuất quá ngắn, có thể có lỗi!")
            
            # Thử tìm trong body nếu nội dung quá ngắn
            body = soup.body
            if body:
                logger.info("Thử trích xuất nội dung từ body")
                for script in body.find_all('script'):
                    script.decompose()
                for style in body.find_all('style'):
                    style.decompose()
                chapter_text = get_clean_text(body)
        
        # Kiểm tra nếu nội dung vẫn quá ngắn
        if len(chapter_text) < 200:
            logger.warning("Nội dung vẫn quá ngắn sau khi trích xuất từ body. Thử giải mã toàn bộ HTML!")
            
            # Thử tìm content ở dạng mã hóa trong toàn bộ HTML
            content_search = re.search(r'content:[\'"`]([^\'"]+)[\'"`]', html_content)
            if content_search:
                encoded_content = content_search.group(1)
                decoded_content = try_decode_content(encoded_content)
                if decoded_content:
                    logger.info("Đã giải mã nội dung từ HTML gốc")
                    chapter_text = get_clean_text(BeautifulSoup(decoded_content, 'html.parser'))
        
        # Kiểm tra xem văn bản có chủ yếu là tiếng Việt không
        vietnamese_chars = re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', chapter_text, re.IGNORECASE)
        if len(vietnamese_chars) < 10 and len(chapter_text) > 500:
            # Nếu có ít ký tự tiếng Việt, có thể là văn bản bị mã hóa sai
            logger.warning("Văn bản có vẻ không phải tiếng Việt, có thể bị mã hóa sai")
        
        # Ghi nội dung vào file với encoding UTF-8 với BOM để hỗ trợ tiếng Việt tốt hơn
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            f.write(f"{title}\n\n{'='*50}\n\n{chapter_text}")
        
        logger.info(f"Đã lưu nội dung vào file: {output_file}")
        return output_file
            
    except Exception as e:
        logger.exception(f"Lỗi khi trích xuất nội dung: {str(e)}")
        return None

def extract_from_js(soup):
    """
    Trích xuất nội dung từ mã JavaScript trong trang
    """
    scripts = soup.find_all('script')
    
    # Tìm biến chapterData
    for script in scripts:
        if not script.string:
            continue
            
        # Tìm script có chứa dữ liệu chương
        if "chapterData" in script.string or "content:" in script.string:
            logger.info("Tìm thấy script chứa dữ liệu chương")
            
            # Tìm kiếm JSON hoặc đối tượng JS
            patterns = [
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
                        logger.info(f"Tìm thấy dữ liệu với pattern: {pattern[:20]}...")
                        
                        if pattern == patterns[0]:  # Đối tượng JavaScript đầy đủ
                            try:
                                # Thay thế undefined thành null để parse JSON
                                content_json = re.sub(r'undefined', 'null', content_data)
                                chapter_data = json.loads(content_json)
                                
                                if 'content' in chapter_data:
                                    content_html = chapter_data['content']
                                    # Giải mã nội dung nếu cần
                                    decoded_content = try_decode_content(content_html)
                                    if decoded_content:
                                        return BeautifulSoup(decoded_content, 'html.parser')
                                    else:
                                        return BeautifulSoup(content_html, 'html.parser')
                            except json.JSONDecodeError as e:
                                logger.warning(f"Lỗi parse JSON: {str(e)}")
                        else:  # Các pattern khác trích xuất trực tiếp chuỗi content
                            encoded_content = content_data
                            decoded_content = try_decode_content(encoded_content)
                            if decoded_content:
                                return BeautifulSoup(decoded_content, 'html.parser')
                except Exception as e:
                    logger.warning(f"Lỗi khi trích xuất với pattern: {str(e)}")
    
    # Tìm kiếm các biến khác có thể chứa nội dung
    content_var_names = ["chapterContent", "chapter_content", "content", "_content"]
    for script in scripts:
        if script.string:
            for var_name in content_var_names:
                patterns = [
                    rf'var\s+{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                    rf'let\s+{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                    rf'const\s+{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                    rf'{var_name}\s*=\s*[\'"`]([^\'"`]+)[\'"`]'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        encoded_content = match.group(1)
                        logger.info(f"Tìm thấy biến {var_name} với nội dung mã hóa")
                        decoded_content = try_decode_content(encoded_content)
                        if decoded_content:
                            return BeautifulSoup(decoded_content, 'html.parser')

    return None

def get_clean_text(element):
    """
    Chuyển đổi nội dung HTML thành văn bản sạch, giữ lại cấu trúc đoạn văn
    """
    if not element:
        return ""
        
    # Loại bỏ các phần tử không mong muốn (như quảng cáo, bình luận...)
    for unwanted in element.select('script, style, iframe, ins, canvas, div#middle-content-one, div#middle-content-two, div#middle-content-three, header, footer, .nav, .menu, .sidebar, .comment'):
        if unwanted:
            unwanted.decompose()
    
    # Loại bỏ các attribute không cần thiết
    for tag in element.find_all(True):
        if tag.name not in ['br', 'p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            tag.unwrap()
    
    # Chuyển đổi HTML thành văn bản, giữ lại các ngắt dòng
    text = ""
    for content in element.contents:
        if content.name == 'br':
            text += '\n'
        elif content.name in ['p', 'div']:
            paragraph_text = content.get_text(strip=True)
            if paragraph_text:
                text += paragraph_text + '\n\n'
        elif content.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Không thêm tiêu đề vào nội dung
            pass
        elif content.string:
            text += content.string.strip() + '\n'
    
    # Xử lý văn bản
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line and not any(phrase in line.lower() for phrase in ['converter', 'edit: ', 'nguồn', 'bản quyền', 'copyright']):
            lines.append(line)
    
    # Loại bỏ các dòng trống liên tiếp
    result = []
    prev_empty = False
    for line in lines:
        if line.strip():
            result.append(line)
            prev_empty = False
        elif not prev_empty:
            result.append("")
            prev_empty = True
    
    # Xóa các nội dung quảng cáo phổ biến
    text = '\n'.join(result)
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
        r'\bx\b'  # Xóa ký tự 'x' đứng một mình (thường là nút đóng)
    ]
    
    for pattern in ad_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Xóa khoảng trắng thừa
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    
    return text

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
    except:
        pass
    
    # Thử decode unicode escape
    try:
        decoded = bytes(encoded_content, 'utf-8').decode('unicode_escape')
        if '<' in decoded and '>' in decoded:  # Có vẻ là HTML
            logger.info("Đã giải mã unicode escape thành công")
            return decoded
    except:
        pass

    # Thử các phương pháp thay thế cụ thể cho metruyencv
    try:
        # MTC sử dụng nhiều bảng thay thế khác nhau tùy theo phiên bản
        # Đây là bảng thay thế phổ biến nhất cho metruyencv
        custom_base64_table = {
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
        }
        
        # Thêm một bảng thay thế thứ hai mà metruyencv đôi khi sử dụng
        custom_base64_table_alt = {
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
        }
        
        # Thử cả hai bảng thay thế
        for table in [custom_base64_table, custom_base64_table_alt]:
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
                    logger.info("Đã giải mã nội dung sử dụng bảng thay thế thành công")
                    return decoded
                # Đôi khi nội dung được mã hóa thêm một lần nữa
                if decoded.startswith('eyJ') or decoded.startswith('e1'):  # Đây thường là dấu hiệu của base64 JSON
                    try:
                        double_decoded = base64.b64decode(decoded).decode('utf-8')
                        if '<' in double_decoded and '>' in double_decoded:
                            logger.info("Đã giải mã nội dung hai lần thành công")
                            return double_decoded
                    except:
                        pass
            except:
                pass
            
    except Exception as e:
        logger.warning(f"Không thể giải mã với phương pháp thay thế: {str(e)}")
    
    # Tìm kiếm nội dung đặc biệt trong chuỗi mã hóa - đôi khi chapterContent ở dạng JSON
    try:
        import re
        import json
        
        # Tìm kiếm mẫu JSON trong chuỗi
        json_pattern = r'\{.*\"content\":\"([^\"]+)\".*\}'
        match = re.search(json_pattern, encoded_content)
        if match:
            content_str = match.group(1)
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
        return encoded_content
        
    # Nếu các phương pháp trên không thành công, coi như không giải mã được
    return None

def extract_all_html_files(input_dir, output_dir=None, combine=False):
    """
    Trích xuất nội dung từ tất cả các file HTML trong thư mục
    
    Args:
        input_dir: Thư mục chứa các file HTML
        output_dir: Thư mục để lưu các file text. Nếu None, sẽ sử dụng input_dir
        combine: Nếu True, sẽ kết hợp tất cả các file thành một file duy nhất
    
    Returns:
        Số lượng file đã xử lý thành công
    """
    try:
        # Nếu không chỉ định output_dir, sử dụng input_dir
        if output_dir is None:
            output_dir = input_dir
        
        # Đảm bảo output_dir tồn tại
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Tìm tất cả các file HTML trong thư mục
        html_files = glob.glob(os.path.join(input_dir, "*.html"))
        html_files.extend(glob.glob(os.path.join(input_dir, "*.htm")))
        
        if not html_files:
            logger.warning(f"Không tìm thấy file HTML nào trong thư mục: {input_dir}")
            return 0
        
        successful = 0
        output_files = []
        
        # Xử lý từng file
        for html_file in html_files:
            # Tạo tên file đầu ra
            base_name = os.path.basename(html_file)
            output_file = os.path.join(output_dir, os.path.splitext(base_name)[0] + ".txt")
            
            # Trích xuất nội dung
            result = extract_story_content(html_file, output_file)
            
            if result:
                successful += 1
                output_files.append(result)
        
        # Kết hợp tất cả file nếu được yêu cầu
        if combine and output_files:
            combined_file = os.path.join(output_dir, "combined_story.txt")
            
            with open(combined_file, 'w', encoding='utf-8') as outfile:
                for output_file in output_files:
                    with open(output_file, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n" + "="*50 + "\n\n")  # Dấu phân cách giữa các chương
            
            logger.info(f"Đã kết hợp {len(output_files)} file vào {combined_file}")
        
        return successful
        
    except Exception as e:
        logger.exception(f"Lỗi khi xử lý các file HTML: {str(e)}")
        return 0 