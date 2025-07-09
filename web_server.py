#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader - Web Interface
Simple Flask web server for manga downloading
"""

import os
import json
import threading
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for
from downloader import get_story_info, get_chapters, download_chapter

app = Flask(__name__)

# Global variables for download status
download_status = {
    'is_downloading': False,
    'current_chapter': '',
    'progress': 0,
    'total_chapters': 0,
    'success_count': 0,
    'story_folder': '',
    'message': '',
    'stop_requested': False
}

@app.route('/')
def index():
    """Trang chủ với form nhập liệu"""
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def start_download():
    """Bắt đầu quá trình tải truyện"""
    global download_status
    
    if download_status['is_downloading']:
        return jsonify({'error': 'Đang có quá trình tải khác đang chạy!'})
    
    # Lấy dữ liệu từ form
    story_url = request.form.get('story_url', '').strip()
    start_chapter = int(request.form.get('start_chapter', 1))
    end_chapter = request.form.get('end_chapter', '')
    browser_choice = request.form.get('browser', 'auto')

    if not story_url:
        return jsonify({'error': 'Vui lòng nhập URL truyện!'})

    # Chuyển đổi end_chapter
    try:
        end_chapter = int(end_chapter) if end_chapter else None
    except ValueError:
        end_chapter = None
    
    # Reset trạng thái
    download_status.update({
        'is_downloading': True,
        'current_chapter': '',
        'progress': 0,
        'total_chapters': 0,
        'success_count': 0,
        'story_folder': '',
        'message': 'Đang khởi tạo...',
        'stop_requested': False
    })
    
    # Chạy download trong thread riêng
    thread = threading.Thread(target=download_worker, args=(story_url, start_chapter, end_chapter, browser_choice))
    thread.daemon = True
    thread.start()
    
    return redirect(url_for('progress'))

@app.route('/progress')
def progress():
    """Trang hiển thị tiến trình tải"""
    return render_template('progress.html')

@app.route('/status')
def get_status():
    """API trả về trạng thái hiện tại"""
    return jsonify(download_status)

@app.route('/stop', methods=['POST'])
def stop_download():
    """Dừng quá trình tải truyện"""
    global download_status

    if download_status['is_downloading']:
        download_status['stop_requested'] = True
        download_status['message'] = 'Đang dừng tiến trình...'
        return jsonify({'success': True, 'message': 'Đã yêu cầu dừng tiến trình'})
    else:
        return jsonify({'success': False, 'message': 'Không có tiến trình nào đang chạy'})

def download_worker(story_url, start_chapter, end_chapter, browser_choice="auto"):
    """Worker function để tải truyện trong background"""
    global download_status

    try:
        # Lấy thông tin truyện
        download_status['message'] = 'Đang lấy thông tin truyện...'
        story_folder = get_story_info(story_url, browser_choice)
        
        if not story_folder:
            download_status.update({
                'is_downloading': False,
                'stop_requested': False,
                'message': 'Lỗi: Không thể lấy thông tin truyện!'
            })
            return
        
        download_status['story_folder'] = story_folder
        
        # Lấy danh sách chương
        download_status['message'] = 'Đang lấy danh sách chương...'
        chapters = get_chapters(story_url, browser_choice)
        
        if not chapters:
            download_status.update({
                'is_downloading': False,
                'stop_requested': False,
                'message': 'Lỗi: Không tìm thấy chương nào!'
            })
            return
        
        # Xác định phạm vi tải
        if end_chapter and end_chapter <= len(chapters):
            chapters_to_download = chapters[start_chapter-1:end_chapter]
        else:
            chapters_to_download = chapters[start_chapter-1:]
        
        download_status['total_chapters'] = len(chapters_to_download)
        download_status['message'] = f'Bắt đầu tải {len(chapters_to_download)} chương...'
        
        # Tải từng chương
        success = 0
        for i, chapter in enumerate(chapters_to_download, 1):
            # Kiểm tra nếu có yêu cầu dừng
            if download_status['stop_requested']:
                download_status.update({
                    'is_downloading': False,
                    'message': f'Đã dừng! Đã tải {success}/{len(chapters_to_download)} chương vào thư mục: {story_folder}'
                })
                return

            download_status.update({
                'current_chapter': chapter['title'],
                'progress': i,
                'message': f'Đang tải: {chapter["title"]}'
            })

            if download_chapter(chapter['url'], chapter['title'], story_folder, browser_choice):
                success += 1

            download_status['success_count'] = success
            time.sleep(1)  # Nghỉ 1 giây
        
        # Hoàn thành
        download_status.update({
            'is_downloading': False,
            'stop_requested': False,
            'message': f'Hoàn thành! Đã tải {success}/{len(chapters_to_download)} chương vào thư mục: {story_folder}'
        })

    except Exception as e:
        download_status.update({
            'is_downloading': False,
            'stop_requested': False,
            'message': f'Lỗi: {str(e)}'
        })

if __name__ == '__main__':
    print("=== MeTruyenCV Downloader Web Interface ===")
    print("Đang khởi động web server...")
    print("Truy cập: http://localhost:3000")
    print("Nhấn Ctrl+C để dừng server")
    
    app.run(host='0.0.0.0', port=3000, debug=False)
