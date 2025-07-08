# -*- coding: utf-8 -*-
"""
Web Downloader Wrapper
Wrapper class để integrate existing downloader với web interface
"""

import asyncio
import time
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Import existing modules
from config_manager import ConfigManager
from logger import DownloadLogger

class WebDownloader:
    """Web wrapper cho existing downloader functionality"""
    
    def __init__(self, config_manager: ConfigManager, socketio=None):
        self.config = config_manager
        self.socketio = socketio
        self.is_running = False
        self.current_progress = 0
        self.total_chapters = 0
        self.current_chapter = 0
        
        # Initialize logger
        app_settings = self.config.get_app_settings()
        if app_settings['enable_detailed_logging']:
            log_file = app_settings['log_file'] if app_settings['log_file'] else None
            self.logger = DownloadLogger("MeTruyenCV_Web", log_file)
        else:
            self.logger = DownloadLogger("MeTruyenCV_Web")
    
    def emit_progress(self, chapter_num: int, total: int, message: str = ""):
        """Emit progress update to web clients"""
        if self.socketio:
            progress = int((chapter_num / total) * 100) if total > 0 else 0
            self.socketio.emit('progress_update', {
                'current_chapter': chapter_num,
                'total_chapters': total,
                'progress': progress,
                'message': message,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
    
    def emit_log(self, message: str, level: str = 'info'):
        """Emit log message to web clients"""
        if self.socketio:
            self.socketio.emit('new_log', {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': level,
                'message': message
            })
        
        # Also log to console/file
        if level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'debug':
            self.logger.debug(message)
        else:
            self.logger.info(message)
    
    def download_novel(self, novel_url: str, start_chapter: int, end_chapter: int) -> bool:
        """Download novel với web progress updates"""
        try:
            self.is_running = True
            self.total_chapters = end_chapter - start_chapter + 1
            
            self.emit_log(f"🚀 Bắt đầu tải truyện: {novel_url}")
            self.emit_log(f"📖 Chapters: {start_chapter} - {end_chapter} ({self.total_chapters} chapters)")
            
            # Import main_config functions
            import main_config
            
            # Run the actual download
            success = asyncio.run(self._run_download(novel_url, start_chapter, end_chapter))
            
            if success:
                self.emit_log("✅ Hoàn thành tải truyện!", 'info')
                self.emit_progress(self.total_chapters, self.total_chapters, "Hoàn thành!")
            else:
                self.emit_log("❌ Lỗi trong quá trình tải", 'error')
            
            return success
            
        except Exception as e:
            self.emit_log(f"❌ Lỗi: {str(e)}", 'error')
            return False
        finally:
            self.is_running = False
    
    async def _run_download(self, novel_url: str, start_chapter: int, end_chapter: int) -> bool:
        """Chạy download process với async"""
        try:
            # Import necessary functions from main_config
            from main_config import (
                get_novel_info, fetch_chapters, create_epub_file,
                missing_chapter, client
            )
            
            self.emit_log("🔍 Đang lấy thông tin truyện...")
            self.emit_progress(0, self.total_chapters, "Đang lấy thông tin truyện...")
            
            # Get novel info
            novel_info = await get_novel_info(novel_url)
            if not novel_info:
                self.emit_log("❌ Không thể lấy thông tin truyện", 'error')
                return False
            
            self.emit_log(f"📚 Tên truyện: {novel_info['title']}")
            self.emit_log(f"✍️ Tác giả: {novel_info['author']}")
            
            # Create output directory
            download_settings = self.config.get_download_settings()
            filename = novel_url.split('/')[-1].replace('-', '')
            path = f"{download_settings['drive']}:/{download_settings['folder']}/{novel_info['title'].replace(':', ',').replace('?', '')}"
            os.makedirs(path, exist_ok=True)
            
            self.emit_log(f"📁 Thư mục lưu: {path}")
            
            # Download chapters
            self.emit_log(f"📥 Bắt đầu tải {self.total_chapters} chapters...")
            
            download_start_time = time.time()
            chapters = await self._fetch_chapters_with_progress(
                start_chapter, end_chapter, novel_info['final_url']
            )
            download_duration = time.time() - download_start_time
            
            valid_chapters = [chapter for chapter in chapters if chapter is not None]
            
            if not valid_chapters:
                self.emit_log("❌ Không tải được chapter nào", 'error')
                return False
            
            self.emit_log(f"✅ Đã tải {len(valid_chapters)}/{self.total_chapters} chapters")
            self.emit_log(f"⏱️ Thời gian tải: {download_duration:.1f}s")
            
            # Create EPUB
            self.emit_log("📖 Đang tạo file EPUB...")
            self.emit_progress(self.total_chapters, self.total_chapters, "Đang tạo EPUB...")
            
            epub_path = await create_epub_file(
                valid_chapters, novel_info, path, filename
            )
            
            if epub_path and os.path.exists(epub_path):
                file_size = os.path.getsize(epub_path) / (1024 * 1024)  # MB
                self.emit_log(f"✅ Đã tạo EPUB: {epub_path}")
                self.emit_log(f"📊 Kích thước file: {file_size:.1f} MB")
                return True
            else:
                self.emit_log("❌ Lỗi tạo file EPUB", 'error')
                return False
                
        except Exception as e:
            self.emit_log(f"❌ Lỗi trong quá trình download: {str(e)}", 'error')
            return False
    
    async def _fetch_chapters_with_progress(self, start_chapter: int, end_chapter: int, novel_url: str):
        """Fetch chapters với progress updates"""
        from main_config import get_chapter_with_selenium
        
        chapters = []
        
        for i in range(start_chapter, end_chapter + 1):
            if not self.is_running:  # Check if stopped
                break
                
            self.current_chapter = i
            chapter_progress = i - start_chapter + 1
            
            self.emit_progress(
                chapter_progress, 
                self.total_chapters, 
                f"Đang tải chapter {i}..."
            )
            
            try:
                chapter_content = await get_chapter_with_selenium(i, novel_url)
                chapters.append(chapter_content)
                
                if chapter_content:
                    self.emit_log(f"✅ Chapter {i}: OK")
                else:
                    self.emit_log(f"⚠️ Chapter {i}: Trống", 'warning')
                    
            except Exception as e:
                self.emit_log(f"❌ Chapter {i}: Lỗi - {str(e)}", 'error')
                chapters.append(None)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.1)
        
        return chapters
    
    def stop_download(self):
        """Dừng download process"""
        self.is_running = False
        self.emit_log("⏹️ Đang dừng download...", 'warning')

# Test function
if __name__ == "__main__":
    config = ConfigManager()
    downloader = WebDownloader(config)
    
    # Test download
    test_url = "https://metruyencv.biz/truyen/test"
    success = downloader.download_novel(test_url, 1, 2)
    print(f"Download result: {success}")
