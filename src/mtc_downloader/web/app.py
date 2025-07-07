#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module chứa ứng dụng web Flask
"""

import os
import threading
import time
import json
import uuid
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file

from mtc_downloader.core.downloader import download_chapter, download_multiple_chapters, download_all_chapters
from mtc_downloader.core.extractor import extract_story_content, extract_all_html_files

# Thiết lập logging
logger = logging.getLogger(__name__)

class MTCWebApp:
    def __init__(self, host='localhost', port=3000, debug=True):
        """
        Khởi tạo ứng dụng web
        
        Args:
            host: Host để chạy ứng dụng
            port: Cổng để chạy ứng dụng
            debug: Chế độ debug
        """
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.debug = debug
        
        # Thư mục lưu trữ tạm thời
        self.upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
        
        # Lưu trạng thái các tác vụ
        self.tasks = {}
        
        # Thiết lập các route
        self._setup_routes()
    
    def _setup_routes(self):
        """Thiết lập các route cho ứng dụng"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/download', methods=['POST'])
        def download():
            url = request.form.get('url')
            mode = request.form.get('mode', 'single')
            num_chapters = int(request.form.get('num_chapters', 1))
            delay = float(request.form.get('delay', 2))
            combine = request.form.get('combine') == 'true'
            
            # Tạo thư mục riêng cho mỗi tác vụ tải
            task_id = str(uuid.uuid4())
            task_folder = os.path.join(self.upload_folder, task_id)
            if not os.path.exists(task_folder):
                os.makedirs(task_folder)
            
            # Khởi tạo trạng thái tác vụ
            self.tasks[task_id] = {
                'status': 'running',
                'progress': 0,
                'message': 'Đang khởi tạo...',
                'files': [],
                'combined_file': None
            }
            
            # Chạy tác vụ tải trong thread riêng
            def run_download():
                try:
                    self.tasks[task_id]['message'] = 'Đang tải truyện...'
                    
                    if mode == 'single':
                        # Tải một chương
                        result = download_chapter(url, os.path.join(task_folder, "chapter.txt"), delay)
                        if result:
                            self.tasks[task_id]['files'].append(os.path.basename(result))
                            self.tasks[task_id]['status'] = 'completed'
                            self.tasks[task_id]['progress'] = 100
                            self.tasks[task_id]['message'] = 'Tải thành công một chương.'
                        else:
                            self.tasks[task_id]['status'] = 'failed'
                            self.tasks[task_id]['message'] = 'Tải thất bại!'
                    
                    elif mode == 'multi':
                        # Tải nhiều chương
                        successful = download_multiple_chapters(url, num_chapters, task_folder, delay, combine)
                        if successful > 0:
                            self.tasks[task_id]['status'] = 'completed'
                            self.tasks[task_id]['progress'] = 100
                            self.tasks[task_id]['message'] = f'Tải thành công {successful}/{num_chapters} chương.'
                            
                            # Cập nhật danh sách file
                            for file in os.listdir(task_folder):
                                if file.endswith('.txt'):
                                    if file == 'combined_story.txt' and combine:
                                        self.tasks[task_id]['combined_file'] = file
                                    else:
                                        self.tasks[task_id]['files'].append(file)
                        else:
                            self.tasks[task_id]['status'] = 'failed'
                            self.tasks[task_id]['message'] = 'Tải thất bại!'
                    
                    else:  # mode == 'all'
                        # Tải tất cả chương
                        successful = download_all_chapters(url, task_folder, delay, combine)
                        if successful > 0:
                            self.tasks[task_id]['status'] = 'completed'
                            self.tasks[task_id]['progress'] = 100
                            self.tasks[task_id]['message'] = f'Tải thành công {successful} chương.'
                            
                            # Cập nhật danh sách file
                            for file in os.listdir(task_folder):
                                if file.endswith('.txt'):
                                    if file == 'combined_story.txt' and combine:
                                        self.tasks[task_id]['combined_file'] = file
                                    else:
                                        self.tasks[task_id]['files'].append(file)
                        else:
                            self.tasks[task_id]['status'] = 'failed'
                            self.tasks[task_id]['message'] = 'Tải thất bại!'
                
                except Exception as e:
                    logger.exception(f"Lỗi khi tải truyện: {str(e)}")
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['message'] = f'Lỗi: {str(e)}'
            
            # Bắt đầu thread tải
            thread = threading.Thread(target=run_download)
            thread.daemon = True
            thread.start()
            
            return jsonify({'task_id': task_id})
        
        @self.app.route('/extract', methods=['POST'])
        def extract():
            # Xử lý upload file HTML
            if 'html_file' not in request.files:
                return jsonify({'error': 'Không có file được tải lên'})
            
            file = request.files['html_file']
            if file.filename == '':
                return jsonify({'error': 'Không có file được chọn'})
            
            # Tạo thư mục riêng cho mỗi tác vụ
            task_id = str(uuid.uuid4())
            task_folder = os.path.join(self.upload_folder, task_id)
            if not os.path.exists(task_folder):
                os.makedirs(task_folder)
            
            # Lưu file HTML tải lên
            html_path = os.path.join(task_folder, file.filename)
            file.save(html_path)
            
            # Khởi tạo trạng thái tác vụ
            self.tasks[task_id] = {
                'status': 'running',
                'progress': 0,
                'message': 'Đang trích xuất...',
                'files': [],
                'combined_file': None
            }
            
            # Chạy tác vụ trích xuất trong thread riêng
            def run_extract():
                try:
                    # Trích xuất nội dung
                    output_file = os.path.join(task_folder, os.path.splitext(file.filename)[0] + '.txt')
                    result = extract_story_content(html_path, output_file)
                    
                    if result:
                        self.tasks[task_id]['files'].append(os.path.basename(result))
                        self.tasks[task_id]['status'] = 'completed'
                        self.tasks[task_id]['progress'] = 100
                        self.tasks[task_id]['message'] = 'Trích xuất thành công.'
                    else:
                        self.tasks[task_id]['status'] = 'failed'
                        self.tasks[task_id]['message'] = 'Trích xuất thất bại!'
                
                except Exception as e:
                    logger.exception(f"Lỗi khi trích xuất nội dung: {str(e)}")
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['message'] = f'Lỗi: {str(e)}'
            
            # Bắt đầu thread trích xuất
            thread = threading.Thread(target=run_extract)
            thread.daemon = True
            thread.start()
            
            return jsonify({'task_id': task_id})
        
        @self.app.route('/task_status/<task_id>')
        def task_status(task_id):
            if task_id not in self.tasks:
                return jsonify({'status': 'not_found'})
            
            return jsonify(self.tasks[task_id])
        
        @self.app.route('/download_file/<task_id>/<filename>')
        def download_file(task_id, filename):
            task_folder = os.path.join(self.upload_folder, task_id)
            file_path = os.path.join(task_folder, filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'File không tồn tại'})
            
            return send_file(file_path, as_attachment=True)
        
        @self.app.route('/view_file/<task_id>/<filename>')
        def view_file(task_id, filename):
            task_folder = os.path.join(self.upload_folder, task_id)
            file_path = os.path.join(task_folder, filename)
            
            if not os.path.exists(file_path):
                return "File không tồn tại", 404
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return render_template('view_file.html', content=content, filename=filename)
            except Exception as e:
                logger.exception(f"Lỗi khi đọc file: {str(e)}")
                return f"Lỗi khi đọc file: {str(e)}", 500
    
    def run(self):
        """Chạy ứng dụng web"""
        # Tạo thư mục templates nếu chưa tồn tại
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            
        # Tạo thư mục static nếu chưa tồn tại
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        
        self.app.run(host=self.host, port=self.port, debug=self.debug)

def create_app(host='localhost', port=3000, debug=True):
    """
    Tạo và trả về ứng dụng web
    
    Args:
        host: Host để chạy ứng dụng
        port: Cổng để chạy ứng dụng
        debug: Chế độ debug
    
    Returns:
        Đối tượng Flask app
    """
    app = MTCWebApp(host, port, debug)
    return app.app

def run_app(host='localhost', port=3000, debug=True):
    """
    Tạo và chạy ứng dụng web
    
    Args:
        host: Host để chạy ứng dụng
        port: Cổng để chạy ứng dụng
        debug: Chế độ debug
    """
    app = MTCWebApp(host, port, debug)
    app.run()

if __name__ == '__main__':
    # Thiết lập logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Chạy ứng dụng
    run_app() 