#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để chạy downloader với output rõ ràng
"""

import sys
import os

# Thêm flush để output hiển thị ngay lập tức
def print_flush(msg):
    print(msg)
    sys.stdout.flush()

print_flush("=== Test MeTruyenCV Downloader ===")

try:
    # Import và chạy main function
    print_flush("Đang import downloader...")
    from downloader import main
    
    print_flush("Đang chạy main function...")
    main()
    
    print_flush("✓ Hoàn thành!")
    
except Exception as e:
    print_flush(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
