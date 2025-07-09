# -*- coding: utf-8 -*-
"""
Config Manager for MeTruyenCV Downloader
Quản lý cấu hình cho MeTruyenCV Downloader
"""

import os
import configparser
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_file: str = "config.txt"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file, encoding='utf-8')
                try:
                    print(f"✅ Đã tải cấu hình từ {self.config_file}")
                except UnicodeEncodeError:
                    print(f"[OK] Da tai cau hinh tu {self.config_file}")
            except Exception as e:
                try:
                    print(f"⚠️  Lỗi đọc config: {e}")
                except UnicodeEncodeError:
                    print(f"[WARNING] Loi doc config: {e}")
                self.create_default_config()
        else:
            try:
                print(f"📝 Tạo file cấu hình mặc định: {self.config_file}")
            except UnicodeEncodeError:
                print(f"[INFO] Tao file cau hinh mac dinh: {self.config_file}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration file"""
        self.config['LOGIN'] = {
            'email': '',
            'password': ''
        }

        self.config['DOWNLOAD'] = {
            'drive': 'C',
            'folder': 'novel',
            'max_connections': '50'
        }

        self.config['LAST_NOVEL'] = {
            'url': '',
            'start_chapter': '1',
            'end_chapter': '1'
        }

        self.config['SETTINGS'] = {
            'auto_save': 'true',
            'headless': 'true',
            'chapter_timeout': '30',
            'retry_attempts': '3',
            'remember_last_novel': 'true',
            'auto_run': 'false'
        }

        self.config['TIMEOUTS'] = {
            'page_load_timeout': '30',
            'element_wait_timeout': '10',
            'image_download_timeout': '60',
            'overall_chapter_timeout': '300',
            'retry_delay_base': '1',
            'max_retry_delay': '30'
        }

        self.config['ADVANCED'] = {
            'user_agent': '',
            'request_delay': '1',
            'use_ocr': 'true',
            'enable_detailed_logging': 'true',
            'log_file': 'download.log'
        }
        
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write("# MeTruyenCV Downloader Configuration\n")
                f.write("# Cấu hình cho MeTruyenCV Downloader\n")
                f.write("# Chỉnh sửa file này để thay đổi cài đặt mặc định\n\n")
                
                # Write config
                self.config.write(f)
                
                # Write footer
                f.write("\n# Ghi chú:\n")
                f.write("# - Để trống các giá trị sẽ sử dụng mặc định\n")
                f.write("# - Thay đổi file này và khởi động lại chương trình\n")
                f.write("# - File này sẽ được tạo lại nếu bị xóa\n")
            
            print(f"✅ Đã lưu cấu hình vào {self.config_file}")
        except Exception as e:
            print(f"❌ Lỗi lưu config: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            value = self.config.get(section, key)
            if value == '':
                return default
            
            # Convert boolean strings
            if value.lower() in ['true', 'false']:
                return value.lower() == 'true'
            
            # Try to convert to int
            try:
                return int(value)
            except ValueError:
                return value
                
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def set(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
    
    def get_login_info(self) -> Dict[str, str]:
        """Get login information"""
        email = self.get('LOGIN', 'email', '')
        password = self.get('LOGIN', 'password', '')
        
        # If not in config, ask user
        if not email:
            email = input('📧 Email tài khoản metruyencv: ')
            if self.get('SETTINGS', 'auto_save', True):
                self.set('LOGIN', 'email', email)
        
        if not password:
            import getpass
            password = getpass.getpass('🔒 Password: ')
            if self.get('SETTINGS', 'auto_save', True):
                self.set('LOGIN', 'password', password)
        
        if self.get('SETTINGS', 'auto_save', True):
            self.save_config()
        
        return {'email': email, 'password': password}
    
    def get_download_settings(self) -> Dict[str, Any]:
        """Get download settings"""
        drive = self.get('DOWNLOAD', 'drive', 'C')
        folder = self.get('DOWNLOAD', 'folder', 'novel')
        max_connections = self.get('DOWNLOAD', 'max_connections', 50)
        
        # Ask user if not in config
        if not self.config.has_option('DOWNLOAD', 'drive') or self.get('DOWNLOAD', 'drive', '') == '':
            drive = input(f'💾 Ổ đĩa lưu truyện (C/D/E) [{drive}]: ').upper() or drive
            if self.get('SETTINGS', 'auto_save', True):
                self.set('DOWNLOAD', 'drive', drive)
        
        if not self.config.has_option('DOWNLOAD', 'max_connections') or self.get('DOWNLOAD', 'max_connections', 0) == 0:
            try:
                max_conn_input = input(f'🔗 Max connections (10-1000) [{max_connections}]: ')
                max_connections = int(max_conn_input) if max_conn_input else max_connections
            except ValueError:
                max_connections = 50
            
            if self.get('SETTINGS', 'auto_save', True):
                self.set('DOWNLOAD', 'max_connections', max_connections)
        
        if self.get('SETTINGS', 'auto_save', True):
            self.save_config()
        
        return {
            'drive': drive,
            'folder': folder,
            'max_connections': max_connections
        }
    
    def get_app_settings(self) -> Dict[str, Any]:
        """Get application settings"""
        return {
            'headless': self.get('SETTINGS', 'headless', True),
            'chapter_timeout': self.get('SETTINGS', 'chapter_timeout', 30),
            'retry_attempts': self.get('SETTINGS', 'retry_attempts', 3),
            'remember_last_novel': self.get('SETTINGS', 'remember_last_novel', True),
            'auto_run': self.get('SETTINGS', 'auto_run', False),
            'user_agent': self.get('ADVANCED', 'user_agent', ''),
            'request_delay': self.get('ADVANCED', 'request_delay', 1),
            'use_ocr': self.get('ADVANCED', 'use_ocr', True),
            'enable_detailed_logging': self.get('ADVANCED', 'enable_detailed_logging', True),
            'log_file': self.get('ADVANCED', 'log_file', 'download.log')
        }

    def get_timeout_settings(self) -> Dict[str, Any]:
        """Get timeout settings"""
        return {
            'page_load_timeout': self.get('TIMEOUTS', 'page_load_timeout', 30),
            'element_wait_timeout': self.get('TIMEOUTS', 'element_wait_timeout', 10),
            'image_download_timeout': self.get('TIMEOUTS', 'image_download_timeout', 60),
            'overall_chapter_timeout': self.get('TIMEOUTS', 'overall_chapter_timeout', 300),
            'retry_delay_base': self.get('TIMEOUTS', 'retry_delay_base', 1),
            'max_retry_delay': self.get('TIMEOUTS', 'max_retry_delay', 30)
        }

    def get_last_novel_info(self) -> Dict[str, Any]:
        """Get last novel information"""
        if not self.get('SETTINGS', 'remember_last_novel', True):
            return {'url': '', 'start_chapter': 1, 'end_chapter': 1}

        return {
            'url': self.get('LAST_NOVEL', 'url', ''),
            'start_chapter': self.get('LAST_NOVEL', 'start_chapter', 1),
            'end_chapter': self.get('LAST_NOVEL', 'end_chapter', 1)
        }

    def save_last_novel_info(self, url: str, start_chapter: int, end_chapter: int):
        """Save last novel information"""
        if self.get('SETTINGS', 'remember_last_novel', True):
            self.set('LAST_NOVEL', 'url', url)
            self.set('LAST_NOVEL', 'start_chapter', start_chapter)
            self.set('LAST_NOVEL', 'end_chapter', end_chapter)

            if self.get('SETTINGS', 'auto_save', True):
                self.save_config()

    def get_novel_input_with_defaults(self) -> Dict[str, Any]:
        """Get novel input with smart defaults from last novel"""
        last_novel = self.get_last_novel_info()

        # Get URL with default
        if last_novel['url']:
            url_prompt = f"📖 Nhập link metruyencv [{last_novel['url']}]: "
            novel_url = input(url_prompt).strip()
            if not novel_url:
                novel_url = last_novel['url']
        else:
            novel_url = input('📖 Nhập link metruyencv mà bạn muốn tải: ').strip()

        # Get start chapter with default
        if last_novel['start_chapter'] > 1:
            start_prompt = f"📄 Chapter bắt đầu [{last_novel['start_chapter']}]: "
            start_input = input(start_prompt).strip()
            start_chapter = int(start_input) if start_input else last_novel['start_chapter']
        else:
            start_chapter = int(input('📄 Chapter bắt đầu: '))

        # Get end chapter with smart default (start + previous range)
        previous_range = last_novel['end_chapter'] - last_novel['start_chapter']
        suggested_end = start_chapter + max(previous_range, 2)  # At least 3 chapters

        end_prompt = f"📄 Chapter kết thúc [{suggested_end}]: "
        end_input = input(end_prompt).strip()
        end_chapter = int(end_input) if end_input else suggested_end

        return {
            'url': novel_url,
            'start_chapter': start_chapter,
            'end_chapter': end_chapter
        }

    def should_auto_run(self) -> bool:
        """Check if should run automatically without user input"""
        return self.get('SETTINGS', 'auto_run', False)

    def enable_auto_run(self):
        """Enable auto run mode"""
        self.set('SETTINGS', 'auto_run', True)
        if self.get('SETTINGS', 'auto_save', True):
            self.save_config()
        print("✅ Đã bật chế độ auto run - Script sẽ tự động chạy theo config")

    def disable_auto_run(self):
        """Disable auto run mode"""
        self.set('SETTINGS', 'auto_run', False)
        if self.get('SETTINGS', 'auto_save', True):
            self.save_config()
        print("✅ Đã tắt chế độ auto run - Script sẽ hỏi input như bình thường")

    def get_auto_run_info(self) -> Dict[str, Any]:
        """Get auto run information from last novel"""
        if not self.should_auto_run():
            return None

        last_novel = self.get_last_novel_info()
        if not last_novel['url']:
            print("⚠️  Auto run enabled nhưng không có novel nào trong lịch sử")
            return None

        # Calculate next chapter range
        previous_range = last_novel['end_chapter'] - last_novel['start_chapter'] + 1
        next_start = last_novel['end_chapter'] + 1
        next_end = next_start + previous_range - 1

        return {
            'url': last_novel['url'],
            'start_chapter': next_start,
            'end_chapter': next_end
        }
    
    def display_config(self):
        """Display current configuration"""
        print("\n" + "="*50)
        print("📋 CURRENT CONFIGURATION")
        print("="*50)
        
        print("\n🔐 LOGIN:")
        email = self.get('LOGIN', 'email', '')
        print(f"  Email: {'*' * len(email) if email else 'Not set'}")
        print(f"  Password: {'*' * 8 if self.get('LOGIN', 'password', '') else 'Not set'}")
        
        print("\n💾 DOWNLOAD:")
        print(f"  Drive: {self.get('DOWNLOAD', 'drive', 'C')}")
        print(f"  Folder: {self.get('DOWNLOAD', 'folder', 'novel')}")
        print(f"  Max connections: {self.get('DOWNLOAD', 'max_connections', 50)}")

        print("\n📚 LAST NOVEL:")
        last_url = self.get('LAST_NOVEL', 'url', '')
        if last_url:
            print(f"  URL: {last_url}")
            print(f"  Chapters: {self.get('LAST_NOVEL', 'start_chapter', 1)} - {self.get('LAST_NOVEL', 'end_chapter', 1)}")
        else:
            print("  No previous novel")

        print("\n⚙️  SETTINGS:")
        print(f"  Auto save: {self.get('SETTINGS', 'auto_save', True)}")
        print(f"  Headless: {self.get('SETTINGS', 'headless', True)}")
        print(f"  Chapter timeout: {self.get('SETTINGS', 'chapter_timeout', 30)}s")
        print(f"  Retry attempts: {self.get('SETTINGS', 'retry_attempts', 3)}")
        print(f"  Remember last novel: {self.get('SETTINGS', 'remember_last_novel', True)}")
        print(f"  Auto run: {self.get('SETTINGS', 'auto_run', False)}")

        print("\n⏱️  TIMEOUTS:")
        print(f"  Page load: {self.get('TIMEOUTS', 'page_load_timeout', 30)}s")
        print(f"  Element wait: {self.get('TIMEOUTS', 'element_wait_timeout', 10)}s")
        print(f"  Image download: {self.get('TIMEOUTS', 'image_download_timeout', 60)}s")
        print(f"  Overall chapter: {self.get('TIMEOUTS', 'overall_chapter_timeout', 300)}s")
        print(f"  Retry delay base: {self.get('TIMEOUTS', 'retry_delay_base', 1)}s")
        print(f"  Max retry delay: {self.get('TIMEOUTS', 'max_retry_delay', 30)}s")

        print("\n🔧 ADVANCED:")
        print(f"  Request delay: {self.get('ADVANCED', 'request_delay', 1)}s")
        print(f"  Use OCR: {self.get('ADVANCED', 'use_ocr', True)}")
        print(f"  Detailed logging: {self.get('ADVANCED', 'enable_detailed_logging', True)}")
        print(f"  Log file: {self.get('ADVANCED', 'log_file', 'download.log')}")

        print("="*50)

# Test function
if __name__ == "__main__":
    config = ConfigManager()
    config.display_config()
    
    print("\nTesting login info...")
    login_info = config.get_login_info()
    print(f"Email: {login_info['email']}")
    
    print("\nTesting download settings...")
    download_settings = config.get_download_settings()
    print(f"Settings: {download_settings}")
    
    config.display_config()
