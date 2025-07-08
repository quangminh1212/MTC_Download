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
                print(f"✅ Đã tải cấu hình từ {self.config_file}")
            except Exception as e:
                print(f"⚠️  Lỗi đọc config: {e}")
                self.create_default_config()
        else:
            print(f"📝 Tạo file cấu hình mặc định: {self.config_file}")
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
        
        self.config['SETTINGS'] = {
            'auto_save': 'true',
            'headless': 'true',
            'chapter_timeout': '30',
            'retry_attempts': '3'
        }
        
        self.config['ADVANCED'] = {
            'user_agent': '',
            'request_delay': '1',
            'use_ocr': 'true'
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
            'user_agent': self.get('ADVANCED', 'user_agent', ''),
            'request_delay': self.get('ADVANCED', 'request_delay', 1),
            'use_ocr': self.get('ADVANCED', 'use_ocr', True)
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
        
        print("\n⚙️  SETTINGS:")
        print(f"  Auto save: {self.get('SETTINGS', 'auto_save', True)}")
        print(f"  Headless: {self.get('SETTINGS', 'headless', True)}")
        print(f"  Chapter timeout: {self.get('SETTINGS', 'chapter_timeout', 30)}s")
        print(f"  Retry attempts: {self.get('SETTINGS', 'retry_attempts', 3)}")
        
        print("\n🔧 ADVANCED:")
        print(f"  Request delay: {self.get('ADVANCED', 'request_delay', 1)}s")
        print(f"  Use OCR: {self.get('ADVANCED', 'use_ocr', True)}")
        
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
