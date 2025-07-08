from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import os
import re
import time
import zipfile
import threading
from queue import Queue

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

            # Debug: In ra status code
            print(f"Response status: {response.status_code}")

            # Lấy tiêu đề chương từ h2 trong trang
            chapter_title = ""
            title_element = soup.find('h2')
            if title_element:
                chapter_title = title_element.get_text().strip()
                print(f"Found title: {chapter_title}")

            # Tìm nội dung chương - thử nhiều cách
            content = ""

            # Cách 1: Tìm theo thẻ main (MeTruyenCV sử dụng main)
            main_element = soup.find('main')
            if main_element:
                print("Found main element")
                # Loại bỏ các thẻ không cần thiết
                for tag in main_element.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()

                content = main_element.get_text(separator='\n').strip()
                print(f"Main content length: {len(content)}")

            # Cách 2: Tìm theo id="chapter-content"
            if not content:
                content_element = soup.find('div', id='chapter-content')
                if content_element:
                    print("Found chapter-content div")
                    for tag in content_element.find_all(['script', 'style']):
                        tag.decompose()

                    content = content_element.get_text(separator='\n').strip()
                    print(f"Chapter-content length: {len(content)}")

            # Cách 3: Tìm div có class chứa "content"
            if not content:
                print("Trying to find content by class...")
                content_divs = soup.find_all('div', class_=lambda x: x and 'content' in str(x).lower())
                for div in content_divs:
                    text = div.get_text().strip()
                    if len(text) > 100:
                        content = text
                        print(f"Found content in div with class: {div.get('class')}")
                        break

            # Cách 4: Tìm tất cả thẻ p và ghép lại
            if not content:
                print("Trying to find content in p tags...")
                paragraphs = soup.find_all('p')
                content_parts = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 10:
                        content_parts.append(text)

                if content_parts:
                    content = '\n\n'.join(content_parts)
                    print(f"Found {len(content_parts)} paragraphs")

            # Kiểm tra xem chương có bị khóa không
            if content and ('- Chương Bị Khóa -' in content or
                           'Bạn có thể mở khóa' in content or
                           'mở khóa bằng' in content or
                           'Chương Bị Khóa' in content):
                print("Chapter is locked - requires payment")
                return {
                    'title': chapter_title,
                    'content': '[CHƯƠNG BỊ KHÓA - CẦN THANH TOÁN]'
                }

            # Làm sạch nội dung
            if content:
                lines = content.split('\n')
                cleaned_lines = []

                # Danh sách từ khóa cần loại bỏ
                skip_keywords = [
                    'javascript', 'function', 'var ', 'document.', 'window.',
                    'cấu hình', 'mục lục', 'đánh dấu', 'cài đặt', 'màu nền', 'màu chữ',
                    'font chữ', 'cỡ chữ', 'chiều cao dòng', 'canh chữ', 'chương trước',
                    'chương sau', 'chấm điểm', 'tặng quà', 'báo cáo', 'đề cử',
                    'đăng nhập', 'đăng ký', 'tài khoản', 'thông báo', 'bình luận',
                    'chia sẻ', 'theo dõi', 'yêu thích', 'bookmark', 'close', '#',
                    'avenir', 'bookerly', 'segoe', 'literata', 'baskerville',
                    'arial', 'courier', 'tahoma', 'palatino', 'georgia', 'verdana',
                    'times new roman', 'source sans', 'canh trái', 'canh đều',
                    'canh giữa', 'canh phải', 'mặc định'
                ]

                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10:  # Tăng độ dài tối thiểu
                        # Kiểm tra xem dòng có chứa từ khóa spam không
                        is_spam = False
                        for keyword in skip_keywords:
                            if keyword.lower() in line.lower():
                                is_spam = True
                                break

                        # Bỏ dòng chỉ chứa số, ký tự đặc biệt, hoặc mã màu
                        if (line.isdigit() or
                            line.startswith('#') or
                            len(line.replace(' ', '')) < 5 or
                            all(c in '#abcdef0123456789ABCDEF' for c in line.replace(' ', ''))):
                            is_spam = True

                        if not is_spam:
                            cleaned_lines.append(line)

                # Ghép lại và làm sạch
                content = '\n\n'.join(cleaned_lines)

                # Loại bỏ nhiều dòng trống liên tiếp
                import re
                content = re.sub(r'\n{3,}', '\n\n', content)

                # Loại bỏ phần đầu và cuối nếu là menu/navigation
                content_lines = content.split('\n\n')
                if len(content_lines) > 3:
                    # Bỏ 2 đoạn đầu và 1 đoạn cuối (thường là menu)
                    content_lines = content_lines[2:-1]
                    content = '\n\n'.join(content_lines)

            print(f"Final content length: {len(content)}")

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
    
    def download_novel(self, novel_url, start_chapter=1, end_chapter=None, progress_id=None, skip_locked=True):
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
                skip_this_chapter = False

                for retry in range(max_retries):
                    try:
                        chapter_data = self.download_chapter(chapter['url'])
                        if chapter_data and chapter_data['content']:
                            # Kiểm tra xem có phải chương bị khóa không
                            if '[CHƯƠNG BỊ KHÓA' in chapter_data['content']:
                                print(f"Chương {chapter['number']} bị khóa - cần thanh toán")
                                if skip_locked:
                                    print(f"Bỏ qua chương {chapter['number']} (bị khóa)")
                                    skip_this_chapter = True
                                    break  # Thoát khỏi vòng lặp retry
                                else:
                                    break  # Vẫn tải chương bị khóa nếu không bỏ qua
                            elif len(chapter_data['content']) > 30:  # Giảm yêu cầu độ dài
                                break

                        print(f"Chương {chapter['number']} - Lần thử {retry + 1}: Nội dung quá ngắn hoặc rỗng")
                        if retry < max_retries - 1:
                            time.sleep(2)
                    except Exception as e:
                        print(f"Chương {chapter['number']} - Lần thử {retry + 1}: Lỗi {e}")
                        if retry < max_retries - 1:
                            time.sleep(2)

                # Nếu cần bỏ qua chương này, tiếp tục với chương tiếp theo
                if skip_this_chapter:
                    continue

                if chapter_data and chapter_data['content'] and len(chapter_data['content']) > 10:
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
    skip_locked = data.get('skip_locked', True)
    
    if not novel_url:
        return jsonify({'error': 'URL không hợp lệ'}), 400
    
    # Tạo progress ID
    progress_id = f"download_{int(time.time())}"
    
    # Chạy download trong thread riêng
    thread = threading.Thread(
        target=downloader.download_novel,
        args=(novel_url, start_chapter, end_chapter, progress_id, skip_locked)
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
