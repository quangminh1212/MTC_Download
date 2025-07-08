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
        """Lấy danh sách chương"""
        try:
            # Thử các pattern URL khác nhau cho danh sách chương
            base_url = novel_url.rstrip('/')
            possible_urls = [
                f"{base_url}/muc-luc",
                f"{base_url}/danh-sach-chuong",
                base_url
            ]
            
            chapters = []
            
            for url in possible_urls:
                try:
                    response = self.session.get(url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Tìm các link chương
                        chapter_links = soup.find_all('a', href=re.compile(r'/chuong-\d+'))
                        
                        if chapter_links:
                            for link in chapter_links:
                                chapter_url = urljoin(url, link.get('href'))
                                chapter_title = link.get_text().strip()
                                
                                # Lấy số chương
                                chapter_match = re.search(r'chuong-(\d+)', chapter_url)
                                chapter_num = int(chapter_match.group(1)) if chapter_match else len(chapters) + 1
                                
                                chapters.append({
                                    'number': chapter_num,
                                    'title': chapter_title,
                                    'url': chapter_url
                                })
                            break
                except:
                    continue
            
            # Nếu không tìm thấy danh sách chương, thử tạo URL dựa trên pattern
            if not chapters:
                # Thử tạo URL cho 50 chương đầu
                for i in range(1, 51):
                    chapter_url = f"{base_url}/chuong-{i}"
                    chapters.append({
                        'number': i,
                        'title': f"Chương {i}",
                        'url': chapter_url
                    })
            
            # Sắp xếp theo số chương
            chapters.sort(key=lambda x: x['number'])
            return chapters
            
        except Exception as e:
            print(f"Error getting chapter list: {e}")
            return []
    
    def download_chapter(self, chapter_url):
        """Tải nội dung một chương"""
        try:
            response = self.session.get(chapter_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Lấy tiêu đề chương
            chapter_title = ""
            title_selectors = [
                'h2',
                '.chapter-title',
                'h1'
            ]

            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    chapter_title = title_element.get_text().strip()
                    break

            # Tìm nội dung chương - MeTruyenCV sử dụng id="chapter-content"
            content = ""
            content_element = soup.find('div', id='chapter-content')

            if content_element:
                # Loại bỏ các thẻ script, style, canvas
                for tag in content_element.find_all(['script', 'style', 'canvas']):
                    tag.decompose()

                # Lấy text và làm sạch
                content = content_element.get_text(separator='\n').strip()

                # Làm sạch nội dung
                lines = content.split('\n')
                cleaned_lines = []

                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Converter') and not line.startswith('-----'):
                        cleaned_lines.append(line)

                content = '\n\n'.join(cleaned_lines)

            # Nếu không tìm thấy với id, thử các selector khác
            if not content:
                content_selectors = [
                    '.chapter-content',
                    '.content',
                    '.story-content',
                    '.reading-content'
                ]

                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        content = content_element.get_text(separator='\n').strip()
                        break

            # Nếu vẫn không có, thử tìm div chứa nhiều paragraph
            if not content:
                divs = soup.find_all('div')
                for div in divs:
                    paragraphs = div.find_all('p')
                    if len(paragraphs) > 3:  # Có nhiều đoạn văn
                        content = div.get_text(separator='\n').strip()
                        break

            return {
                'title': chapter_title,
                'content': content
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
            for i, chapter in enumerate(chapters):
                if progress_id:
                    self.progress[progress_id]['current'] = i + 1
                    self.progress[progress_id]['message'] = f'Đang tải {chapter["title"]}...'

                chapter_data = self.download_chapter(chapter['url'])
                if chapter_data and chapter_data['content']:
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
                else:
                    print(f"Không thể tải chương {chapter['number']}: {chapter['title']}")

                # Delay để tránh spam
                time.sleep(2)  # Tăng delay lên 2 giây
            
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
                self.progress[progress_id]['message'] = f'Hoàn thành! Đã tải {len(downloaded_chapters)} chương'
                self.progress[progress_id]['download_url'] = f'/download/{zip_filename}'
            
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
