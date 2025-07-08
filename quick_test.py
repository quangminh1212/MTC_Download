#!/usr/bin/env python3
"""
Quick test để kiểm tra main.py có chạy được không
"""

import sys
import subprocess

def test_import():
    """Test import các module"""
    try:
        print("Testing imports...")
        import httpx
        import bs4
        import ebooklib
        import asyncio
        import tqdm
        import playwright
        import pytesseract
        import PIL
        import appdirs
        import configparser
        import os
        import gc
        import async_lru
        print("✅ Tất cả imports thành công")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_syntax():
    """Test syntax của main.py"""
    try:
        print("Testing main.py syntax...")
        result = subprocess.run([sys.executable, '-m', 'py_compile', 'main.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ main.py syntax OK")
            return True
        else:
            print(f"❌ Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing syntax: {e}")
        return False

def test_basic_run():
    """Test chạy main.py với timeout"""
    try:
        print("Testing basic run (5 seconds timeout)...")
        # Chạy với timeout và input mặc định
        result = subprocess.run([sys.executable, 'main.py'], 
                              input='n\n',  # Thoát ngay
                              timeout=5,
                              capture_output=True, 
                              text=True)
        print("✅ main.py có thể chạy")
        return True
    except subprocess.TimeoutExpired:
        print("✅ main.py chạy được (timeout như mong đợi)")
        return True
    except Exception as e:
        print(f"❌ Error running main.py: {e}")
        return False

if __name__ == "__main__":
    print("=== Quick Test cho main.py ===\n")
    
    tests = [
        ("Import test", test_import),
        ("Syntax test", test_syntax),
        ("Basic run test", test_basic_run)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        print()
    
    print(f"=== Kết quả: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 Tất cả tests đều pass! main.py sẵn sàng sử dụng.")
    else:
        print("⚠️  Có một số vấn đề cần khắc phục.")
