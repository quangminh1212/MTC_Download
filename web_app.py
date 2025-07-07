#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import os
import threading
import time
import json
from download_story import download_chapter, download_multiple_chapters, download_all_chapters
from extract_story import extract_story_content
from extract_story_batch import extract_all_html_files
import uuid

app = Flask(__name__)

# Thư mục lưu trữ tạm thời
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Lưu trạng thái các tác vụ
tasks = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    mode = request.form.get('mode', 'single')
    num_chapters = int(request.form.get('num_chapters', 1))
    delay = float(request.form.get('delay', 2))
    combine = request.form.get('combine') == 'true'
    
    # Tạo thư mục riêng cho mỗi tác vụ tải
    task_id = str(uuid.uuid4())
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    if not os.path.exists(task_folder):
        os.makedirs(task_folder)
    
    # Khởi tạo trạng thái tác vụ
    tasks[task_id] = {
        'status': 'running',
        'progress': 0,
        'message': 'Đang khởi tạo...',
        'files': [],
        'combined_file': None
    }
    
    # Chạy tác vụ tải trong thread riêng
    def run_download():
        try:
            tasks[task_id]['message'] = 'Đang tải truyện...'
            
            if mode == 'single':
                # Tải một chương
                result = download_chapter(url, os.path.join(task_folder, "chapter.txt"), delay)
                if result:
                    tasks[task_id]['files'].append(os.path.basename(result))
                    tasks[task_id]['status'] = 'completed'
                    tasks[task_id]['progress'] = 100
                    tasks[task_id]['message'] = 'Tải thành công một chương.'
                else:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['message'] = 'Tải thất bại!'
            
            elif mode == 'multi':
                # Tải nhiều chương
                successful = download_multiple_chapters(url, num_chapters, task_folder, delay, combine)
                if successful > 0:
                    tasks[task_id]['status'] = 'completed'
                    tasks[task_id]['progress'] = 100
                    tasks[task_id]['message'] = f'Tải thành công {successful}/{num_chapters} chương.'
                    
                    # Cập nhật danh sách file
                    for file in os.listdir(task_folder):
                        if file.endswith('.txt'):
                            if file == 'combined_story.txt' and combine:
                                tasks[task_id]['combined_file'] = file
                            else:
                                tasks[task_id]['files'].append(file)
                else:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['message'] = 'Tải thất bại!'
            
            else:  # mode == 'all'
                # Tải tất cả chương
                successful = download_all_chapters(url, task_folder, delay, combine)
                if successful > 0:
                    tasks[task_id]['status'] = 'completed'
                    tasks[task_id]['progress'] = 100
                    tasks[task_id]['message'] = f'Tải thành công {successful} chương.'
                    
                    # Cập nhật danh sách file
                    for file in os.listdir(task_folder):
                        if file.endswith('.txt'):
                            if file == 'combined_story.txt' and combine:
                                tasks[task_id]['combined_file'] = file
                            else:
                                tasks[task_id]['files'].append(file)
                else:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['message'] = 'Tải thất bại!'
        
        except Exception as e:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['message'] = f'Lỗi: {str(e)}'
    
    # Bắt đầu thread tải
    thread = threading.Thread(target=run_download)
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/extract', methods=['POST'])
def extract():
    # Xử lý upload file HTML
    if 'html_file' not in request.files:
        return jsonify({'error': 'Không có file được tải lên'})
    
    file = request.files['html_file']
    if file.filename == '':
        return jsonify({'error': 'Không có file được chọn'})
    
    # Tạo thư mục riêng cho mỗi tác vụ
    task_id = str(uuid.uuid4())
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    if not os.path.exists(task_folder):
        os.makedirs(task_folder)
    
    # Lưu file HTML tải lên
    html_path = os.path.join(task_folder, file.filename)
    file.save(html_path)
    
    # Khởi tạo trạng thái tác vụ
    tasks[task_id] = {
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
                tasks[task_id]['files'].append(os.path.basename(result))
                tasks[task_id]['status'] = 'completed'
                tasks[task_id]['progress'] = 100
                tasks[task_id]['message'] = 'Trích xuất thành công.'
            else:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['message'] = 'Trích xuất thất bại!'
        
        except Exception as e:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['message'] = f'Lỗi: {str(e)}'
    
    # Bắt đầu thread trích xuất
    thread = threading.Thread(target=run_extract)
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/task_status/<task_id>')
def task_status(task_id):
    if task_id not in tasks:
        return jsonify({'status': 'not_found'})
    
    return jsonify(tasks[task_id])

@app.route('/download_file/<task_id>/<filename>')
def download_file(task_id, filename):
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    file_path = os.path.join(task_folder, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File không tồn tại'})
    
    return send_file(file_path, as_attachment=True)

@app.route('/view_file/<task_id>/<filename>')
def view_file(task_id, filename):
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    file_path = os.path.join(task_folder, filename)
    
    if not os.path.exists(file_path):
        return "File không tồn tại", 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return render_template('view_file.html', content=content, filename=filename)
    except Exception as e:
        return f"Lỗi khi đọc file: {str(e)}", 500

if __name__ == '__main__':
    # Tạo thư mục templates nếu chưa tồn tại
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    app.run(host='localhost', port=3000, debug=True) 