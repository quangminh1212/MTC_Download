#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demo offline cho MeTruyenCV Downloader
Sử dụng dữ liệu mẫu để test giao diện
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import time
import zipfile
import threading
from queue import Queue

app = Flask(__name__)

# Dữ liệu mẫu
SAMPLE_NOVELS = {
    'https://metruyencv.com/truyen/no-le-bong-toi': {
        'title': 'Nô Lệ Bóng Tối',
        'author': 'Guiltythree',
        'chapters': [
            {'number': 1, 'title': 'Chương 1: Nightmare Begins - Khởi Đầu Ác Mộng', 'content': '''Lớn lên trong cảnh nghèo khó, Sunny chưa bao giờ kỳ vọng điều gì tốt đẹp từ cuộc sống.

Tuy nhiên, ngay cả cậu cũng không ngờ rằng mình lại được lựa chọn bởi Nightmare Spell (Ác Mộng Ma Pháp) và trở thành một trong những Awakened (Người Thức Tỉnh)– một nhóm tinh anh sở hữu năng lực siêu nhiên.

Bị đưa vào một magical world (thế giới ma thuật) đổ nát, Sunny phải đối mặt với những quái vật khủng khiếp – và cả những Người Thức Tỉnh khác – trong một trận chiến sinh tồn chết chóc.

Tệ hơn nữa là, sức mạnh thần thánh mà cậu nhận được lại có một tác dụng phụ nhỏ, nhưng có khả năng gây ra tử vong chí mạng…'''},
            {'number': 2, 'title': 'Chương 2: The First Nightmare', 'content': '''Sunny tỉnh dậy trong một căn phòng tối tăm, xung quanh là những bức tường đá lạnh lẽo. Cậu cảm thấy một sức mạnh kỳ lạ chảy trong người mình.

"Chào mừng đến với Nightmare Spell," một giọng nói vang lên trong đầu cậu.

Cậu nhìn quanh và thấy một con quái vật khổng lồ đang tiến về phía mình...'''},
            {'number': 3, 'title': 'Chương 3: Shadow Bond', 'content': '''Sunny học được cách sử dụng sức mạnh bóng tối của mình. Cậu có thể điều khiển bóng tối và biến chúng thành vũ khí.

Nhưng mỗi lần sử dụng sức mạnh, cậu cảm thấy một phần linh hồn mình bị nuốt chửng bởi bóng tối...'''}
        ]
    },
    'https://metruyencv.com/truyen/ta-co-mot-toa-thanh-pho-ngay-tan-the': {
        'title': 'Ta Có Một Tòa Thành Phố Ngày Tận Thế',
        'author': 'Đầu Phát Điệu Liễu',
        'chapters': [
            {'number': 1, 'title': 'Chương 1: Tiến vào trò chơi', 'content': '''Tống Kiện nhặt lên mới vừa rồi người nọ ném xuống đất tuyên truyền trang, run hai cái, mặt không cảm giác hướng hạ một người đi đường đi tới.

Sau khi tốt nghiệp làm hơn một tháng tiêu thụ, tiền không kiếm được nhiều ít, thu hoạch duy nhất chính là da mặt dầy liền rất nhiều.

"Vị này nữ sĩ, đầu tiên, mời tiếp nhận ta thành khẩn chúc phúc, đây là ta công ty..." Tống Kiện trên mặt mang nụ cười lễ phép.'''},
            {'number': 2, 'title': 'Chương 2: Da mặt dày là cái quỷ gì?', 'content': '''Tống Kiện tiếp tục công việc phát truyền đơn của mình. Nhưng cuộc sống không như ý muốn.

Một ngày nọ, cậu gặp một ông lão bí ẩn bán game thủ đô...'''},
            {'number': 3, 'title': 'Chương 3: Thành phố tận thế', 'content': '''Tống Kiện bị hút vào game và phát hiện mình đang ở trong một thành phố tận thế thực sự.

Xung quanh là zombie và quái vật. Cậu phải tìm cách sinh tồn...'''}
        ]
    }
}

class DemoDownloader:
    def __init__(self):
        self.progress = {}
        
    def get_novel_info(self, novel_url):
        """Lấy thông tin truyện từ dữ liệu mẫu"""
        if novel_url in SAMPLE_NOVELS:
            data = SAMPLE_NOVELS[novel_url]
            return {
                'title': data['title'],
                'author': data['author'],
                'url': novel_url
            }
        return None
    
    def get_chapter_list(self, novel_url):
        """Lấy danh sách chương từ dữ liệu mẫu"""
        if novel_url in SAMPLE_NOVELS:
            chapters = []
            for chapter in SAMPLE_NOVELS[novel_url]['chapters']:
                chapters.append({
                    'number': chapter['number'],
                    'title': chapter['title'],
                    'url': f"{novel_url}/chuong-{chapter['number']}"
                })
            return chapters
        return []
    
    def download_chapter(self, chapter_url):
        """Tải nội dung một chương từ dữ liệu mẫu"""
        for novel_url, novel_data in SAMPLE_NOVELS.items():
            if chapter_url.startswith(novel_url):
                chapter_num = int(chapter_url.split('-')[-1])
                for chapter in novel_data['chapters']:
                    if chapter['number'] == chapter_num:
                        return {
                            'title': chapter['title'],
                            'content': chapter['content']
                        }
        return {'title': '', 'content': ''}
    
    def clean_filename(self, filename):
        """Làm sạch tên file"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        return filename.strip()[:100]
    
    def download_novel(self, novel_url, start_chapter=1, end_chapter=None, progress_id=None):
        """Tải toàn bộ truyện từ dữ liệu mẫu"""
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
                    self.progress[progress_id]['message'] = 'URL không hợp lệ hoặc không có trong demo'
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
                
                # Delay để mô phỏng quá trình tải
                time.sleep(1)
            
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
            return None

# Khởi tạo downloader
downloader = DemoDownloader()

@app.route('/')
def index():
    return render_template('demo.html')

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
    print("🚀 Demo MeTruyenCV Downloader")
    print("📚 Dữ liệu mẫu có sẵn:")
    for url, data in SAMPLE_NOVELS.items():
        print(f"  - {data['title']} ({len(data['chapters'])} chương)")
        print(f"    URL: {url}")
    print("\n🌐 Truy cập: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
