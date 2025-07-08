# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader Web Interface
Giao diện web cho MeTruyenCV Downloader
"""

import os
import json
import threading
import time
import traceback
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, g
from flask_socketio import SocketIO, emit
import eventlet

# Import existing modules
from config_manager import ConfigManager
from logger import DownloadLogger

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

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)

# Simple in-memory cache
class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key, default=None):
        if key in self._cache:
            # Check if expired (5 minutes default)
            if time.time() - self._timestamps[key] < 300:
                return self._cache[key]
            else:
                # Remove expired entry
                del self._cache[key]
                del self._timestamps[key]
        return default

    def set(self, key, value, ttl=300):
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def delete(self, key):
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]

    def clear(self):
        self._cache.clear()
        self._timestamps.clear()

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_times = []
        self.error_count = 0
        self.total_requests = 0

    def record_request(self, duration):
        self.request_times.append(duration)
        self.total_requests += 1

        # Keep only last 100 requests
        if len(self.request_times) > 100:
            self.request_times.pop(0)

    def record_error(self):
        self.error_count += 1

    def get_stats(self):
        if not self.request_times:
            return {'avg_response_time': 0, 'error_rate': 0}

        avg_time = sum(self.request_times) / len(self.request_times)
        error_rate = (self.error_count / self.total_requests) * 100 if self.total_requests > 0 else 0

        return {
            'avg_response_time': round(avg_time, 3),
            'error_rate': round(error_rate, 2),
            'total_requests': self.total_requests
        }

# Global variables
config_manager = ConfigManager()
cache = SimpleCache()
perf_monitor = PerformanceMonitor()

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

# Performance middleware
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        perf_monitor.record_request(duration)

        # Log slow requests
        if duration > 1.0:
            app.logger.warning(f'Slow request: {request.endpoint} took {duration:.3f}s')

    # Add performance headers
    response.headers['X-Response-Time'] = f'{duration:.3f}s' if hasattr(g, 'start_time') else 'unknown'
    response.headers['X-Total-Requests'] = str(perf_monitor.total_requests)

    # Add caching headers for static content
    if request.endpoint and 'static' in request.endpoint:
        response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hour
    elif request.endpoint and request.endpoint.startswith('api_'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

    # Add compression hint
    if response.content_length and response.content_length > 1024:
        response.headers['Vary'] = 'Accept-Encoding'

    return response

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f'404 error: {request.url}')
    return render_template('error.html',
                         error_code=404,
                         error_message='Trang không tồn tại'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 error: {str(error)}')
    return render_template('error.html',
                         error_code=500,
                         error_message='Lỗi server nội bộ'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {str(e)}')
    app.logger.error(traceback.format_exc())
    return render_template('error.html',
                         error_code=500,
                         error_message='Đã xảy ra lỗi không mong muốn'), 500

# Routes
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
    last_novel = config_manager.get_last_novel()
    return render_template('download.html', 
                         last_novel=last_novel,
                         status=download_status)

@app.route('/logs')
def logs_page():
    """Trang xem logs"""
    return render_template('logs.html', logs=download_status['logs'])

@app.route('/performance')
def performance_page():
    """Trang performance monitoring"""
    return render_template('performance.html')

# API Routes
@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API để get/set configuration"""
    try:
        if request.method == 'GET':
            app.logger.info('Getting configuration')

            # Try cache first
            cached_config = cache.get('config_data')
            if cached_config:
                return jsonify({
                    'success': True,
                    'data': cached_config,
                    'cached': True
                })

            # Get fresh data
            config_data = {
                'login': config_manager.get_login_info(),
                'download': config_manager.get_download_settings(),
                'settings': config_manager.get_app_settings(),
                'timeouts': config_manager.get_timeout_settings()
            }

            # Cache for 5 minutes
            cache.set('config_data', config_data, 300)

            return jsonify({
                'success': True,
                'data': config_data,
                'cached': False
            })

        elif request.method == 'POST':
            app.logger.info('Updating configuration')

            if not request.is_json:
                return jsonify({'success': False, 'message': 'Content-Type phải là application/json'}), 400

            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Dữ liệu JSON không hợp lệ'}), 400

            # Validate data structure
            valid_sections = ['login', 'download', 'settings', 'timeouts']
            for section in data.keys():
                if section not in valid_sections:
                    return jsonify({'success': False, 'message': f'Section không hợp lệ: {section}'}), 400

            # Update configuration
            for section, values in data.items():
                if not isinstance(values, dict):
                    return jsonify({'success': False, 'message': f'Dữ liệu section {section} phải là object'}), 400

                for key, value in values.items():
                    config_manager.set(section.upper(), key, value)

            config_manager.save_config()

            # Invalidate cache
            cache.delete('config_data')

            app.logger.info('Configuration updated successfully')
            return jsonify({'success': True, 'message': 'Cấu hình đã được lưu'})

    except Exception as e:
        app.logger.error(f'Error in api_config: {str(e)}')
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/start_download', methods=['POST'])
def api_start_download():
    """API để bắt đầu download"""
    try:
        if download_status['is_downloading']:
            app.logger.warning('Download request rejected - already downloading')
            return jsonify({'success': False, 'message': 'Đang có download khác chạy'}), 409

        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type phải là application/json'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dữ liệu JSON không hợp lệ'}), 400

        # Validate input
        novel_url = data.get('url', '').strip()
        if not novel_url:
            return jsonify({'success': False, 'message': 'URL không được để trống'}), 400

        # Validate URL format
        valid_domains = ['metruyencv.biz', 'metruyencv.com', 'metruyencv.info']
        if not any(domain in novel_url for domain in valid_domains):
            return jsonify({'success': False, 'message': 'URL không hợp lệ. Chỉ hỗ trợ metruyencv.biz/com/info'}), 400

        try:
            start_chapter = int(data.get('start_chapter', 1))
            end_chapter = int(data.get('end_chapter', 1))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Chapter phải là số nguyên'}), 400

        # Validate chapter range
        if start_chapter < 1:
            return jsonify({'success': False, 'message': 'Chapter bắt đầu phải >= 1'}), 400

        if end_chapter < start_chapter:
            return jsonify({'success': False, 'message': 'Chapter kết thúc phải >= chapter bắt đầu'}), 400

        if end_chapter - start_chapter > 1000:
            return jsonify({'success': False, 'message': 'Không thể tải quá 1000 chapters cùng lúc'}), 400

        app.logger.info(f'Starting download: {novel_url}, chapters {start_chapter}-{end_chapter}')

        # Save last novel info
        config_manager.set('LAST_NOVEL', 'url', novel_url)
        config_manager.set('LAST_NOVEL', 'start_chapter', str(start_chapter))
        config_manager.set('LAST_NOVEL', 'end_chapter', str(end_chapter))
        config_manager.save_config()

        # Start download in background thread
        download_thread = threading.Thread(
            target=start_download_background,
            args=(novel_url, start_chapter, end_chapter),
            name='DownloadThread'
        )
        download_thread.daemon = True
        download_thread.start()

        return jsonify({'success': True, 'message': 'Bắt đầu download'})

    except Exception as e:
        app.logger.error(f'Error in api_start_download: {str(e)}')
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/stop_download', methods=['POST'])
def api_stop_download():
    """API để dừng download"""
    download_status['is_downloading'] = False
    download_status['status_message'] = 'Đã dừng'
    socketio.emit('download_stopped', {'message': 'Download đã được dừng'})
    return jsonify({'success': True, 'message': 'Đã dừng download'})

@app.route('/api/status')
def api_status():
    """API để lấy trạng thái hiện tại"""
    try:
        return jsonify({
            'success': True,
            'data': download_status
        })
    except Exception as e:
        app.logger.error(f'Error in api_status: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/error_report', methods=['POST'])
def api_error_report():
    """API để nhận báo cáo lỗi từ client"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type phải là application/json'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dữ liệu JSON không hợp lệ'}), 400

        # Log error report
        app.logger.error(f"Client error report: {json.dumps(data, indent=2)}")

        return jsonify({'success': True, 'message': 'Báo cáo lỗi đã được ghi nhận'})

    except Exception as e:
        app.logger.error(f'Error in api_error_report: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/config/backup', methods=['GET'])
def api_config_backup():
    """API để backup cấu hình"""
    try:
        app.logger.info('Creating config backup')

        backup_data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'config': {
                'login': config_manager.get_login_info(),
                'download': config_manager.get_download_settings(),
                'settings': config_manager.get_app_settings(),
                'timeouts': config_manager.get_timeout_settings()
            }
        }

        # Remove sensitive data from backup
        if 'password' in backup_data['config']['login']:
            backup_data['config']['login']['password'] = '***HIDDEN***'

        return jsonify({
            'success': True,
            'data': backup_data,
            'filename': f'metruyencv_config_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        })

    except Exception as e:
        app.logger.error(f'Error in api_config_backup: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi tạo backup: {str(e)}'}), 500

@app.route('/api/config/restore', methods=['POST'])
def api_config_restore():
    """API để restore cấu hình từ backup"""
    try:
        app.logger.info('Restoring config from backup')

        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type phải là application/json'}), 400

        backup_data = request.get_json()
        if not backup_data:
            return jsonify({'success': False, 'message': 'Dữ liệu backup không hợp lệ'}), 400

        # Validate backup format
        if 'config' not in backup_data:
            return jsonify({'success': False, 'message': 'Format backup không hợp lệ'}), 400

        config_data = backup_data['config']

        # Restore configuration (skip password if hidden)
        for section, values in config_data.items():
            if not isinstance(values, dict):
                continue

            for key, value in values.items():
                # Skip hidden passwords
                if key == 'password' and value == '***HIDDEN***':
                    continue

                config_manager.set(section.upper(), key, value)

        config_manager.save_config()
        app.logger.info('Config restored successfully')

        return jsonify({'success': True, 'message': 'Khôi phục cấu hình thành công'})

    except Exception as e:
        app.logger.error(f'Error in api_config_restore: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi khôi phục: {str(e)}'}), 500

@app.route('/api/performance', methods=['GET'])
def api_performance():
    """API để lấy performance statistics"""
    try:
        stats = perf_monitor.get_stats()

        # Add cache stats
        cache_stats = {
            'cache_size': len(cache._cache),
            'cache_keys': list(cache._cache.keys())
        }

        # Add system info
        import psutil
        system_stats = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('.').percent
        }

        return jsonify({
            'success': True,
            'data': {
                'performance': stats,
                'cache': cache_stats,
                'system': system_stats,
                'download_status': download_status
            }
        })

    except ImportError:
        # psutil not available, return basic stats
        return jsonify({
            'success': True,
            'data': {
                'performance': perf_monitor.get_stats(),
                'cache': {
                    'cache_size': len(cache._cache),
                    'cache_keys': list(cache._cache.keys())
                },
                'download_status': download_status
            }
        })

    except Exception as e:
        app.logger.error(f'Error in api_performance: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/cache/clear', methods=['POST'])
def api_cache_clear():
    """API để xóa cache"""
    try:
        cache.clear()
        app.logger.info('Cache cleared')
        return jsonify({'success': True, 'message': 'Cache đã được xóa'})

    except Exception as e:
        app.logger.error(f'Error in api_cache_clear: {str(e)}')
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Xử lý khi client kết nối"""
    emit('status_update', download_status)

@socketio.on('disconnect')
def handle_disconnect():
    """Xử lý khi client ngắt kết nối"""
    pass

def start_download_background(novel_url, start_chapter, end_chapter):
    """Chạy download trong background thread"""
    try:
        # Import web_downloader here to avoid circular import
        from web_downloader import WebDownloader
        
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
        
        socketio.emit('download_started', download_status)
        
        # Create downloader instance
        downloader = WebDownloader(config_manager, socketio)
        
        # Start download
        success = downloader.download_novel(novel_url, start_chapter, end_chapter)
        
        # Update final status
        download_status.update({
            'is_downloading': False,
            'status_message': 'Hoàn thành' if success else 'Lỗi',
            'progress': 100 if success else download_status['progress']
        })
        
        socketio.emit('download_completed', {
            'success': success,
            'status': download_status
        })
        
    except Exception as e:
        download_status.update({
            'is_downloading': False,
            'status_message': f'Lỗi: {str(e)}',
        })
        socketio.emit('download_error', {
            'error': str(e),
            'status': download_status
        })

def add_log(message, level='info'):
    """Thêm log message"""
    log_entry = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'level': level,
        'message': message
    }
    download_status['logs'].append(log_entry)
    
    # Keep only last 100 logs
    if len(download_status['logs']) > 100:
        download_status['logs'] = download_status['logs'][-100:]
    
    # Emit to clients
    socketio.emit('new_log', log_entry)

if __name__ == '__main__':
    print("🌐 Khởi động MeTruyenCV Web Interface...")
    print("📱 Truy cập: http://localhost:5000")
    print("🔧 Cấu hình: http://localhost:5000/config")
    print("📥 Download: http://localhost:5000/download")
    print("📋 Logs: http://localhost:5000/logs")
    print("\n⏹️  Nhấn Ctrl+C để dừng server")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
