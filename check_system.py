#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Check Script for MeTruyenCV Web Interface
Kiểm tra hệ thống và dependencies
"""

import sys
import os
import platform
import subprocess
import importlib
import json
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🔍 MeTruyenCV Web Interface - System Check")
    print("=" * 60)

def print_section(title):
    print(f"\n📋 {title}")
    print("-" * 40)

def check_python():
    """Kiểm tra Python version"""
    print_section("Python Environment")
    
    version = sys.version_info
    print(f"✅ Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Cần Python 3.8 trở lên")
        return False
    
    print(f"✅ Python executable: {sys.executable}")
    print(f"✅ Platform: {platform.platform()}")
    print(f"✅ Architecture: {platform.architecture()[0]}")
    
    return True

def check_virtual_env():
    """Kiểm tra virtual environment"""
    print_section("Virtual Environment")
    
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✅ Đang chạy trong virtual environment")
        print(f"✅ Virtual env path: {sys.prefix}")
    else:
        print("⚠️  Không chạy trong virtual environment")
        print("💡 Khuyến nghị sử dụng virtual environment")
    
    return True

def check_dependencies():
    """Kiểm tra dependencies"""
    print_section("Dependencies Check")
    
    # Main dependencies
    main_deps = [
        'selenium',
        'bs4',  # beautifulsoup4
        'lxml',
        'httpx',
        'ebooklib',
        'configparser'
    ]
    
    # Web dependencies
    web_deps = [
        'flask',
        'flask_socketio',
        'eventlet'
    ]
    
    all_deps = main_deps + web_deps
    missing_deps = []
    
    for dep in all_deps:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n❌ Thiếu {len(missing_deps)} dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n💡 Chạy: pip install -r requirements.txt && pip install -r requirements_web.txt")
        return False
    
    print(f"\n✅ Tất cả {len(all_deps)} dependencies đã được cài đặt")
    return True

def check_files():
    """Kiểm tra files cần thiết"""
    print_section("Required Files")
    
    required_files = [
        'app.py',
        'web_downloader.py',
        'config_manager.py',
        'logger.py',
        'main_config.py',
        'requirements.txt',
        'requirements_web.txt'
    ]
    
    required_dirs = [
        'templates',
        'static',
        'static/css',
        'static/js',
        'static/img'
    ]
    
    missing_files = []
    
    # Check files
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    # Check directories
    for dir in required_dirs:
        if os.path.exists(dir) and os.path.isdir(dir):
            print(f"✅ {dir}/")
        else:
            print(f"❌ {dir}/ - MISSING")
            missing_files.append(dir)
    
    if missing_files:
        print(f"\n❌ Thiếu {len(missing_files)} files/directories")
        return False
    
    return True

def check_config():
    """Kiểm tra config file"""
    print_section("Configuration")
    
    if os.path.exists('config.txt'):
        print("✅ config.txt exists")
        
        try:
            from config_manager import ConfigManager
            config = ConfigManager()
            
            # Test config sections
            login_info = config.get_login_info()
            download_settings = config.get_download_settings()
            app_settings = config.get_app_settings()
            
            print("✅ Config file is readable")
            print(f"✅ Email configured: {'Yes' if login_info.get('email') else 'No'}")
            print(f"✅ Download folder: {download_settings.get('drive')}:/{download_settings.get('folder')}")
            print(f"✅ Headless mode: {app_settings.get('headless')}")
            
        except Exception as e:
            print(f"❌ Config file error: {str(e)}")
            return False
    else:
        print("⚠️  config.txt not found")
        print("💡 Sẽ được tạo tự động khi chạy lần đầu")
    
    return True

def check_ports():
    """Kiểm tra ports"""
    print_section("Network Ports")
    
    import socket
    
    def is_port_open(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    
    # Check port 5000 (default Flask port)
    if is_port_open(5000):
        print("⚠️  Port 5000 đang được sử dụng")
        print("💡 Web server có thể cần port khác")
    else:
        print("✅ Port 5000 available")
    
    return True

def check_browser():
    """Kiểm tra browser cho Selenium"""
    print_section("Browser Support")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Test Chrome
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.quit()
            print("✅ Chrome/Chromium available")
            return True
        except Exception as e:
            print(f"❌ Chrome/Chromium error: {str(e)}")
    
    except ImportError:
        print("❌ Selenium not installed")
    
    return False

def generate_report():
    """Tạo báo cáo hệ thống"""
    print_section("System Report")
    
    report = {
        'timestamp': str(Path().resolve()),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': platform.platform(),
        'architecture': platform.architecture()[0],
        'working_directory': str(Path().resolve()),
        'virtual_env': hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    }
    
    try:
        with open('system_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("✅ System report saved to system_report.json")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")

def main():
    """Main check function"""
    print_header()
    
    checks = [
        ("Python", check_python),
        ("Virtual Environment", check_virtual_env),
        ("Dependencies", check_dependencies),
        ("Files", check_files),
        ("Configuration", check_config),
        ("Network", check_ports),
        ("Browser", check_browser)
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_section("Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"📊 Checks passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 Hệ thống sẵn sàng cho web interface!")
        print("💡 Chạy: python app.py hoặc ./run_web.bat")
    else:
        print("⚠️  Một số vấn đề cần được khắc phục")
        print("💡 Chạy setup script để tự động cài đặt")
    
    # Generate report
    generate_report()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
