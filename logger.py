# -*- coding: utf-8 -*-
"""
Enhanced Logging Utility for MeTruyenCV Downloader
Tiện ích ghi log nâng cao cho MeTruyenCV Downloader
"""

import logging
import sys
from datetime import datetime
from typing import Optional
import threading
from pathlib import Path

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    # Emoji mapping
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '✅', 
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '💥'
    }
    
    def format(self, record):
        # Add timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Get color and emoji
        level_name = record.levelname
        color = self.COLORS.get(level_name, self.COLORS['RESET'])
        emoji = self.EMOJIS.get(level_name, '📝')
        reset = self.COLORS['RESET']
        
        # Format message
        message = record.getMessage()
        
        # Add context if available
        context = getattr(record, 'context', '')
        if context:
            context = f"[{context}] "
        
        return f"{color}{timestamp} {emoji} {context}{message}{reset}"

class DownloadLogger:
    """Enhanced logger for download operations with progress tracking"""
    
    def __init__(self, name: str = "MeTruyenCV", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            try:
                Path(log_file).parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Không thể tạo log file: {e}")
        
        # Thread lock for thread safety
        self._lock = threading.Lock()
        
        # Progress tracking
        self._current_chapter = None
        self._total_chapters = 0
        self._completed_chapters = 0
        self._current_operation = None
    
    def _log_with_context(self, level: int, message: str, context: str = None):
        """Log message with optional context"""
        with self._lock:
            extra = {'context': context} if context else {}
            self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, context: str = None):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, context)
    
    def info(self, message: str, context: str = None):
        """Log info message"""
        self._log_with_context(logging.INFO, message, context)
    
    def warning(self, message: str, context: str = None):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, context)
    
    def error(self, message: str, context: str = None):
        """Log error message"""
        self._log_with_context(logging.ERROR, message, context)
    
    def critical(self, message: str, context: str = None):
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, message, context)
    
    def start_chapter_download(self, chapter_number: int, total_chapters: int = None):
        """Start tracking chapter download progress"""
        with self._lock:
            self._current_chapter = chapter_number
            if total_chapters:
                self._total_chapters = total_chapters
            
            progress = ""
            if self._total_chapters > 0:
                progress = f" ({self._completed_chapters + 1}/{self._total_chapters})"
            
            self.info(f"Bắt đầu tải chapter {chapter_number}{progress}", f"CH{chapter_number}")
    
    def complete_chapter_download(self, chapter_number: int, success: bool = True, content_length: int = None):
        """Complete chapter download tracking"""
        with self._lock:
            if success:
                self._completed_chapters += 1
                status = "thành công"
                if content_length:
                    status += f" - {content_length} ký tự"
                self.info(f"Hoàn thành chapter {chapter_number} {status}", f"CH{chapter_number}")
            else:
                self.error(f"Thất bại tải chapter {chapter_number}", f"CH{chapter_number}")
            
            self._current_chapter = None
    
    def log_operation_start(self, operation: str, context: str = None):
        """Log start of an operation"""
        with self._lock:
            self._current_operation = operation
            self.debug(f"Bắt đầu: {operation}", context)
    
    def log_operation_complete(self, operation: str, duration: float = None, context: str = None):
        """Log completion of an operation"""
        with self._lock:
            duration_str = f" ({duration:.2f}s)" if duration else ""
            self.debug(f"Hoàn thành: {operation}{duration_str}", context)
            self._current_operation = None
    
    def log_timeout(self, operation: str, timeout_value: float, context: str = None):
        """Log timeout event"""
        self.warning(f"Timeout {operation} sau {timeout_value}s", context)
    
    def log_retry(self, operation: str, attempt: int, max_attempts: int, delay: float = None, context: str = None):
        """Log retry attempt"""
        delay_str = f" (chờ {delay:.1f}s)" if delay else ""
        self.warning(f"Thử lại {operation} - lần {attempt}/{max_attempts}{delay_str}", context)
    
    def log_image_progress(self, current: int, total: int, context: str = None):
        """Log image download progress"""
        if total > 0:
            percentage = (current / total) * 100
            self.info(f"Tải ảnh {current}/{total} ({percentage:.1f}%)", context)
    
    def log_page_load(self, url: str, duration: float = None, context: str = None):
        """Log page loading"""
        duration_str = f" ({duration:.2f}s)" if duration else ""
        self.debug(f"Tải trang: {url}{duration_str}", context)
    
    def log_element_found(self, selector: str, attempt: int = 1, context: str = None):
        """Log element found"""
        attempt_str = f" (lần {attempt})" if attempt > 1 else ""
        self.debug(f"Tìm thấy element: {selector}{attempt_str}", context)
    
    def log_element_not_found(self, selector: str, timeout: float = None, context: str = None):
        """Log element not found"""
        timeout_str = f" sau {timeout}s" if timeout else ""
        self.warning(f"Không tìm thấy element: {selector}{timeout_str}", context)
    
    def get_progress_summary(self) -> str:
        """Get current progress summary"""
        with self._lock:
            if self._total_chapters > 0:
                percentage = (self._completed_chapters / self._total_chapters) * 100
                return f"Tiến độ: {self._completed_chapters}/{self._total_chapters} chapters ({percentage:.1f}%)"
            return f"Đã hoàn thành: {self._completed_chapters} chapters"

# Global logger instance
logger = DownloadLogger()

# Convenience functions for backward compatibility
def log_info(message: str, context: str = None):
    logger.info(message, context)

def log_warning(message: str, context: str = None):
    logger.warning(message, context)

def log_error(message: str, context: str = None):
    logger.error(message, context)

def log_debug(message: str, context: str = None):
    logger.debug(message, context)
