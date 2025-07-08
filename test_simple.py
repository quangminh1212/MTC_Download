#!/usr/bin/env python3
"""
Script test đơn giản để kiểm tra các import cơ bản
"""

def test_imports():
    """Test import các module cần thiết"""
    print("Testing imports...")
    
    try:
        import httpx
        print("✅ httpx")
    except ImportError as e:
        print(f"❌ httpx: {e}")
    
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4")
    except ImportError as e:
        print(f"❌ beautifulsoup4: {e}")
    
    try:
        from ebooklib import epub
        print("✅ ebooklib")
    except ImportError as e:
        print(f"❌ ebooklib: {e}")
    
    try:
        import asyncio
        print("✅ asyncio (built-in)")
    except ImportError as e:
        print(f"❌ asyncio: {e}")
    
    try:
        from tqdm import tqdm
        print("✅ tqdm")
    except ImportError as e:
        print(f"❌ tqdm: {e}")
    
    try:
        import backoff
        print("✅ backoff")
    except ImportError as e:
        print(f"❌ backoff: {e}")
    
    try:
        from playwright.async_api import async_playwright
        print("✅ playwright")
    except ImportError as e:
        print(f"❌ playwright: {e}")
    
    try:
        import pytesseract
        print("✅ pytesseract")
    except ImportError as e:
        print(f"❌ pytesseract: {e}")
    
    try:
        from PIL import Image
        print("✅ Pillow")
    except ImportError as e:
        print(f"❌ Pillow: {e}")
    
    try:
        from appdirs import user_config_dir
        print("✅ appdirs")
    except ImportError as e:
        print(f"❌ appdirs: {e}")
    
    try:
        from async_lru import alru_cache
        print("✅ async-lru")
    except ImportError as e:
        print(f"❌ async-lru: {e}")
    
    try:
        import lxml
        print("✅ lxml")
    except ImportError as e:
        print(f"❌ lxml: {e}")

def test_user_agent():
    """Test user-agent module"""
    print("\nTesting user-agent module...")
    try:
        from user_agent import get
        user_agent = get()
        print(f"✅ user-agent module works: {user_agent[:50]}...")
    except Exception as e:
        print(f"❌ user-agent module: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 SIMPLE TEST - MeTruyenCV Downloader")
    print("=" * 50)
    
    test_imports()
    test_user_agent()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)
    
    input("\nPress Enter to exit...")
