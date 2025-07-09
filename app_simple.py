# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader Web Interface - Simple Version
Giao diện web đơn giản cho MeTruyenCV Downloader
"""

import socket
import threading
import time
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Import existing modules
from config_manager import ConfigManager

def find_free_port(start_port=5000, max_port=5100):
    """Tìm port khả dụng"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                s.listen(1)
                return port
        except OSError:
            continue
    return None

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'metruyencv_downloader_secret_key_2024'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
app.logger.setLevel(logging.INFO)

# Global variables
config_manager = ConfigManager()

download_status = {
    'is_downloading': False,
    'current_novel': None,
    'progress': 0,
    'total_chapters': 0,
    'current_chapter': 0,
    'status_message': 'Sẵn sàng',
    'start_time': None,
    'logs': []
}

@app.route('/')
def index():
    """Dashboard chính"""
    return render_template('index.html', 
                         status=download_status,
                         config=config_manager.get_app_settings())

@app.route('/config')
def config_page():
    """Trang cấu hình"""
    return render_template('config.html')

@app.route('/download')
def download_page():
    """Trang download"""
    last_novel = {
        'url': config_manager.get('LAST_NOVEL', 'url', ''),
        'start_chapter': config_manager.get('LAST_NOVEL', 'start_chapter', 1),
        'end_chapter': config_manager.get('LAST_NOVEL', 'end_chapter', 1)
    }
    return render_template('download.html', last_novel=last_novel)

@app.route('/logs')
def logs_page():
    """Trang logs"""
    return render_template('logs.html')

@app.route('/api/config', methods=['GET'])
def api_config_get():
    """API để lấy cấu hình"""
    try:
        config = {
            'login': config_manager.get_login_info(),
            'download': config_manager.get_download_settings(),
            'settings': config_manager.get_app_settings(),
            'timeouts': config_manager.get_timeout_settings()
        }
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        app.logger.error(f'Error in api_config_get: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/config', methods=['POST'])
def api_config_save():
    """API để lưu cấu hình"""
    try:
        data = request.get_json()
        
        # Save login info
        if 'login' in data:
            login = data['login']
            config_manager.set('LOGIN', 'email', login.get('email', ''))
            config_manager.set('LOGIN', 'password', login.get('password', ''))
        
        # Save download settings
        if 'download' in data:
            download = data['download']
            config_manager.set('DOWNLOAD', 'drive', download.get('drive', 'C'))
            config_manager.set('DOWNLOAD', 'folder', download.get('folder', 'novel'))
            config_manager.set('DOWNLOAD', 'max_connections', download.get('max_connections', 50))
        
        # Save app settings
        if 'settings' in data:
            settings = data['settings']
            config_manager.set('SETTINGS', 'headless', settings.get('headless', True))
            config_manager.set('SETTINGS', 'chapter_timeout', settings.get('chapter_timeout', 30))
            config_manager.set('SETTINGS', 'retry_attempts', settings.get('retry_attempts', 3))
            config_manager.set('SETTINGS', 'remember_last_novel', settings.get('remember_last_novel', True))
            config_manager.set('SETTINGS', 'auto_run', settings.get('auto_run', False))
        
        # Save timeout settings
        if 'timeouts' in data:
            timeouts = data['timeouts']
            config_manager.set('TIMEOUTS', 'page_load_timeout', timeouts.get('page_load_timeout', 30))
            config_manager.set('TIMEOUTS', 'element_wait_timeout', timeouts.get('element_wait_timeout', 10))
            config_manager.set('TIMEOUTS', 'image_download_timeout', timeouts.get('image_download_timeout', 60))
            config_manager.set('TIMEOUTS', 'overall_chapter_timeout', timeouts.get('overall_chapter_timeout', 300))
            config_manager.set('TIMEOUTS', 'retry_delay_base', timeouts.get('retry_delay_base', 1))
            config_manager.set('TIMEOUTS', 'max_retry_delay', timeouts.get('max_retry_delay', 30))
        
        # Save config to file
        config_manager.save_config()
        
        app.logger.info('Configuration saved successfully')
        return jsonify({'success': True, 'message': 'Cấu hình đã được lưu'})
        
    except Exception as e:
        app.logger.error(f'Error in api_config_save: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """API để lấy trạng thái download"""
    try:
        return jsonify({'success': True, 'status': download_status})
    except Exception as e:
        app.logger.error(f'Error in api_status: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/download/start', methods=['POST'])
def api_download_start():
    """API để bắt đầu download"""
    try:
        data = request.get_json()
        novel_url = data.get('novel_url', '').strip()
        start_chapter = int(data.get('start_chapter', 1))
        end_chapter = int(data.get('end_chapter', 1))
        
        if not novel_url:
            return jsonify({'success': False, 'message': 'URL truyện không được để trống'}), 400
        
        if start_chapter > end_chapter:
            return jsonify({'success': False, 'message': 'Chapter bắt đầu phải nhỏ hơn hoặc bằng chapter kết thúc'}), 400
        
        if download_status['is_downloading']:
            return jsonify({'success': False, 'message': 'Đang có download khác đang chạy'}), 400
        
        if end_chapter - start_chapter > 1000:
            return jsonify({'success': False, 'message': 'Không thể tải quá 1000 chapters cùng lúc'}), 400
        
        app.logger.info(f'Starting download: {novel_url}, chapters {start_chapter}-{end_chapter}')
        
        # Save last novel info
        config_manager.set('LAST_NOVEL', 'url', novel_url)
        config_manager.set('LAST_NOVEL', 'start_chapter', str(start_chapter))
        config_manager.set('LAST_NOVEL', 'end_chapter', str(end_chapter))
        config_manager.save_config()
        
        # Update status
        download_status.update({
            'is_downloading': True,
            'current_novel': novel_url,
            'progress': 0,
            'total_chapters': end_chapter - start_chapter + 1,
            'current_chapter': start_chapter,
            'status_message': 'Đang khởi tạo...',
            'start_time': datetime.now(),
            'logs': []
        })
        
        return jsonify({'success': True, 'message': 'Bắt đầu download (chức năng sẽ được thêm sau)'})
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Chapter phải là số'}), 400
    except Exception as e:
        app.logger.error(f'Error in api_download_start: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

def start_server():
    """Khởi động server"""
    import sys
    
    # Tìm port khả dụng
    port = find_free_port()
    if port is None:
        print("❌ Không thể tìm thấy port khả dụng từ 5000-5100", flush=True)
        print("💡 Hãy đóng các ứng dụng khác đang sử dụng port này", flush=True)
        return False
    
    print("🌐 Khởi động MeTruyenCV Web Interface...", flush=True)
    print(f"📱 Truy cập: http://localhost:{port}", flush=True)
    print(f"🔧 Cấu hình: http://localhost:{port}/config", flush=True)
    print(f"📥 Download: http://localhost:{port}/download", flush=True)
    print(f"📋 Logs: http://localhost:{port}/logs", flush=True)
    print("\n⏹️  Nhấn Ctrl+C để dừng server", flush=True)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
        return True
    except KeyboardInterrupt:
        print("\n🛑 Server đã dừng", flush=True)
        return True
    except Exception as e:
        print(f"❌ Lỗi khởi động server: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = start_server()
    if not success:
        input("Nhấn Enter để thoát...")
        exit(1)
