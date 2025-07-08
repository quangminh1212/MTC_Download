from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import os
import re
import time
import zipfile
from urllib.parse import urljoin, urlparse
import threading
from queue import Queue
import json

app = Flask(__name__)

class NovelDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.download_queue = Queue()
        self.progress = {}
        
    def get_novel_info(self, novel_url):
        """Lấy thông tin truyện"""
        try:
            response = self.session.get(novel_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Lấy tên truyện
            title_element = soup.find('h1') or soup.find('title')
            title = title_element.get_text().strip() if title_element else "Unknown Novel"
            
            # Lấy tác giả
            author_element = soup.find('a', href=re.compile(r'/tac-gia/'))
            author = author_element.get_text().strip() if author_element else "Unknown Author"
            
            return {
                'title': self.clean_filename(title),
                'author': author,
                'url': novel_url
            }
        except Exception as e:
            print(f"Error getting novel info: {e}")
            return None
    
    def get_chapter_list(self, novel_url):
        """Lấy danh sách chương từ MeTruyenCV"""
        try:
            base_url = novel_url.rstrip('/')
            chapters = []

            print(f"Đang lấy danh sách chương từ: {base_url}")

            # Thử tải trang chính của truyện
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Tìm thông tin về số chương mới nhất
            latest_chapter = 1

            # Tìm trong các thẻ có thể chứa thông tin chương
            for element in soup.find_all(['span', 'div', 'a']):
                text = element.get_text()
                # Tìm pattern "Chương X" hoặc "Chapter X"
                chapter_match = re.search(r'(?:chương|chapter)\s*(\d+)', text.lower())
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                    if chapter_num > latest_chapter:
                        latest_chapter = chapter_num

            # Nếu không tìm thấy, thử tìm số trong URL hoặc text
            if latest_chapter == 1:
                for element in soup.find_all(['a', 'span']):
                    href = element.get('href', '')
                    text = element.get_text()

                    # Tìm trong href
                    if '/chuong-' in href:
                        chapter_match = re.search(r'/chuong-(\d+)', href)
                        if chapter_match:
                            chapter_num = int(chapter_match.group(1))
                            if chapter_num > latest_chapter:
                                latest_chapter = chapter_num

                    # Tìm số lớn trong text (có thể là số chương)
                    numbers = re.findall(r'\b(\d+)\b', text)
                    for num_str in numbers:
                        num = int(num_str)
                        if 1 <= num <= 10000 and num > latest_chapter:  # Giới hạn hợp lý
                            latest_chapter = num

            print(f"Phát hiện có khoảng {latest_chapter} chương")

            # Tạo danh sách chương dựa trên số chương phát hiện được
            # Giới hạn tối đa 2000 chương để tránh spam
            max_chapters = min(latest_chapter, 2000)

            for i in range(1, max_chapters + 1):
                chapter_url = f"{base_url}/chuong-{i}"
                chapters.append({
                    'number': i,
                    'title': f"Chương {i}",
                    'url': chapter_url
                })

            # Nếu không phát hiện được chương nào, tạo 100 chương mặc định
            if not chapters:
                print("Không phát hiện được số chương, tạo 100 chương mặc định")
                for i in range(1, 101):
                    chapter_url = f"{base_url}/chuong-{i}"
                    chapters.append({
                        'number': i,
                        'title': f"Chương {i}",
                        'url': chapter_url
                    })

            print(f"Đã tạo danh sách {len(chapters)} chương")
            return chapters

        except Exception as e:
            print(f"Error getting chapter list: {e}")
            # Fallback: tạo 50 chương mặc định
            base_url = novel_url.rstrip('/')
            chapters = []
            for i in range(1, 51):
                chapter_url = f"{base_url}/chuong-{i}"
                chapters.append({
                    'number': i,
                    'title': f"Chương {i}",
                    'url': chapter_url
                })
            return chapters
    
    def download_chapter(self, chapter_url):
        """Tải nội dung một chương"""
        try:
            # Thêm delay ngẫu nhiên để tránh bị block
            import random
            time.sleep(random.uniform(1, 3))

            response = self.session.get(chapter_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Lấy tiêu đề chương từ h2 trong trang
            chapter_title = ""
            title_element = soup.find('h2')
            if title_element:
                chapter_title = title_element.get_text().strip()

            # Tìm nội dung chương - MeTruyenCV sử dụng id="chapter-content"
            content = ""
            content_element = soup.find('div', id='chapter-content')

            if content_element:
                # Loại bỏ các thẻ không cần thiết
                for tag in content_element.find_all(['script', 'style', 'canvas', 'div']):
                    # Giữ lại div có class chứa nội dung, loại bỏ div khác
                    if tag.name == 'div':
                        div_class = tag.get('class', [])
                        div_id = tag.get('id', '')
                        # Loại bỏ div quảng cáo và không cần thiết
                        if any(keyword in str(div_class) + str(div_id) for keyword in
                               ['ad', 'advertisement', 'banner', 'popup', 'modal', 'config', 'menu']):
                            tag.decompose()
                    else:
                        tag.decompose()

                # Lấy text và làm sạch
                raw_content = content_element.get_text(separator='\n')

                # Làm sạch nội dung chi tiết
                lines = raw_content.split('\n')
                cleaned_lines = []

                skip_patterns = [
                    'Converter', '-----', 'Cấu hình', 'Mục lục', 'Đánh dấu',
                    'Cài đặt đọc truyện', 'Close', 'Màu nền', 'Màu chữ',
                    'Font chữ', 'Cỡ chữ', 'Chiều cao dòng', 'Canh chữ',
                    'Chương bị khóa', 'Bạn có thể mở khóa', 'KNBs',
                    'Chương trước', 'Chương sau', 'Chấm điểm', 'Tặng quà',
                    'Báo cáo', 'Đề cử', 'MTC là nền tảng', 'Điều khoản',
                    'Chính sách', 'Về bản quyền', 'Hướng dẫn sử dụng',
                    'Đăng truyện', 'Kho truyện', 'Xếp hạng', 'Thời gian thực',
                    'Đánh giá mới', '#F8FAFC', '#f4f4f4', 'Avenir Next',
                    'Bookerly', 'Segoe UI', 'Literata', 'Baskerville',
                    'Arial', 'Courier New', 'Tahoma', 'Palatino Linotype',
                    'Georgia', 'Verdana', 'Times New Roman', 'Source Sans Pro',
                    'Canh trái', 'Canh đều', 'Canh giữa', 'Canh phải',
                    'Mặc định', 'Nhập số', 'Đổi', 'sang', 'ở đây'
                ]

                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3:  # Bỏ dòng quá ngắn
                        # Kiểm tra xem dòng có chứa pattern cần bỏ không
                        should_skip = False
                        for pattern in skip_patterns:
                            if pattern.lower() in line.lower():
                                should_skip = True
                                break

                        # Bỏ dòng chỉ chứa số hoặc ký tự đặc biệt
                        if line.isdigit() or all(c in '#%' for c in line):
                            should_skip = True

                        if not should_skip:
                            cleaned_lines.append(line)

                # Ghép lại với khoảng trắng phù hợp
                content = '\n\n'.join(cleaned_lines)

                # Làm sạch thêm: loại bỏ nhiều dòng trống liên tiếp
                import re
                content = re.sub(r'\n{3,}', '\n\n', content)

            # Nếu không tìm thấy nội dung hoặc nội dung quá ngắn, thử cách khác
            if not content or len(content) < 100:
                # Thử tìm trong các thẻ p
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text().strip()
                        if len(text) > 20:  # Chỉ lấy đoạn văn có độ dài hợp lý
                            content_parts.append(text)

                    if content_parts:
                        content = '\n\n'.join(content_parts)

            return {
                'title': chapter_title,
                'content': content.strip()
            }

        except Exception as e:
            print(f"Error downloading chapter {chapter_url}: {e}")
            return {
                'title': '',
                'content': ''
            }
    
    def clean_filename(self, filename):
        """Làm sạch tên file"""
        # Loại bỏ ký tự không hợp lệ
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.strip()
        return filename[:100]  # Giới hạn độ dài
    
    def download_novel(self, novel_url, start_chapter=1, end_chapter=None, progress_id=None):
        """Tải toàn bộ truyện"""
        try:
            # Khởi tạo progress
            if progress_id:
                self.progress[progress_id] = {
                    'status': 'starting',
                    'current': 0,
                    'total': 0,
                    'message': 'Đang lấy thông tin truyện...'
                }
            
            # Lấy thông tin truyện
            novel_info = self.get_novel_info(novel_url)
            if not novel_info:
                if progress_id:
                    self.progress[progress_id]['status'] = 'error'
                    self.progress[progress_id]['message'] = 'Không thể lấy thông tin truyện'
                return None
            
            # Lấy danh sách chương
            if progress_id:
                self.progress[progress_id]['message'] = 'Đang lấy danh sách chương...'
            
            chapters = self.get_chapter_list(novel_url)
            if not chapters:
                if progress_id:
                    self.progress[progress_id]['status'] = 'error'
                    self.progress[progress_id]['message'] = 'Không thể lấy danh sách chương'
                return None
            
            # Lọc chương theo range
            if end_chapter:
                chapters = [c for c in chapters if start_chapter <= c['number'] <= end_chapter]
            else:
                chapters = [c for c in chapters if c['number'] >= start_chapter]
            
            if progress_id:
                self.progress[progress_id]['total'] = len(chapters)
                self.progress[progress_id]['status'] = 'downloading'
            
            # Tạo thư mục
            novel_dir = f"downloads/{novel_info['title']}"
            os.makedirs(novel_dir, exist_ok=True)
            
            # Tải từng chương
            downloaded_chapters = []
            failed_chapters = []

            for i, chapter in enumerate(chapters):
                if progress_id:
                    self.progress[progress_id]['current'] = i + 1
                    self.progress[progress_id]['message'] = f'Đang tải {chapter["title"]} ({i+1}/{len(chapters)})...'

                print(f"Đang tải chương {chapter['number']}: {chapter['url']}")

                # Thử tải chương với retry
                max_retries = 3
                chapter_data = None

                for retry in range(max_retries):
                    try:
                        chapter_data = self.download_chapter(chapter['url'])
                        if chapter_data and chapter_data['content'] and len(chapter_data['content']) > 50:
                            break
                        else:
                            print(f"Chương {chapter['number']} - Lần thử {retry + 1}: Nội dung quá ngắn hoặc rỗng")
                            if retry < max_retries - 1:
                                time.sleep(2)
                    except Exception as e:
                        print(f"Chương {chapter['number']} - Lần thử {retry + 1}: Lỗi {e}")
                        if retry < max_retries - 1:
                            time.sleep(2)

                if chapter_data and chapter_data['content'] and len(chapter_data['content']) > 50:
                    # Sử dụng tiêu đề từ nội dung nếu có, nếu không dùng tiêu đề từ danh sách
                    chapter_title = chapter_data['title'] if chapter_data['title'] else chapter['title']

                    # Lưu thành file txt
                    filename = f"Chuong_{chapter['number']:03d}_{self.clean_filename(chapter_title)}.txt"
                    filepath = os.path.join(novel_dir, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"{chapter_title}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(chapter_data['content'])

                    downloaded_chapters.append({
                        'number': chapter['number'],
                        'title': chapter_title,
                        'file': filepath
                    })

                    print(f"✅ Đã tải thành công chương {chapter['number']} ({len(chapter_data['content'])} ký tự)")
                else:
                    failed_chapters.append(chapter['number'])
                    print(f"❌ Không thể tải chương {chapter['number']}: {chapter['title']}")

                # Delay để tránh spam
                time.sleep(2)
            
            # Tạo file zip
            if progress_id:
                self.progress[progress_id]['message'] = 'Đang tạo file zip...'
            
            zip_filename = f"{novel_info['title']}.zip"
            zip_path = os.path.join("downloads", zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for chapter in downloaded_chapters:
                    zipf.write(chapter['file'], os.path.basename(chapter['file']))
            
            if progress_id:
                self.progress[progress_id]['status'] = 'completed'
                success_msg = f'Hoàn thành! Đã tải {len(downloaded_chapters)} chương'
                if failed_chapters:
                    success_msg += f' (Thất bại: {len(failed_chapters)} chương)'
                self.progress[progress_id]['message'] = success_msg
                self.progress[progress_id]['download_url'] = f'/download/{zip_filename}'
                self.progress[progress_id]['failed_chapters'] = failed_chapters
            
            return {
                'novel_info': novel_info,
                'chapters': downloaded_chapters,
                'zip_file': zip_path
            }
            
        except Exception as e:
            if progress_id:
                self.progress[progress_id]['status'] = 'error'
                self.progress[progress_id]['message'] = f'Lỗi: {str(e)}'
            print(f"Error downloading novel: {e}")
            return None

# Khởi tạo downloader
downloader = NovelDownloader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.json
    novel_url = data.get('url')
    start_chapter = int(data.get('start_chapter', 1))
    end_chapter = int(data.get('end_chapter')) if data.get('end_chapter') else None
    
    if not novel_url:
        return jsonify({'error': 'URL không hợp lệ'}), 400
    
    # Tạo progress ID
    progress_id = f"download_{int(time.time())}"
    
    # Chạy download trong thread riêng
    thread = threading.Thread(
        target=downloader.download_novel,
        args=(novel_url, start_chapter, end_chapter, progress_id)
    )
    thread.start()
    
    return jsonify({'progress_id': progress_id})

@app.route('/api/progress/<progress_id>')
def api_progress(progress_id):
    progress = downloader.progress.get(progress_id, {
        'status': 'not_found',
        'message': 'Không tìm thấy tiến trình'
    })
    return jsonify(progress)

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join("downloads", filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
