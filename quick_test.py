#!/usr/bin/env python3
"""
Quick test script để kiểm tra dependencies
"""

print("=" * 50)
print("🧪 QUICK TEST - MeTruyenCV Downloader")
print("=" * 50)
print()

# Test basic imports
print("Testing basic imports...")
try:
    import sys
    print(f"✅ Python {sys.version}")
except:
    print("❌ Python import failed")

try:
    import httpx
    print("✅ httpx")
except ImportError:
    print("❌ httpx - Run: pip install httpx")

try:
    from bs4 import BeautifulSoup
    print("✅ beautifulsoup4")
except ImportError:
    print("❌ beautifulsoup4 - Run: pip install beautifulsoup4")

try:
    import playwright
    print("✅ playwright")
    # Test playwright install
    try:
        from playwright.sync_api import sync_playwright
        print("  ✅ playwright sync_api")
    except:
        print("  ⚠️  playwright browsers may need installation")
        print("     Run: python -m playwright install firefox")
except ImportError:
    print("❌ playwright - Run: pip install playwright")

try:
    import pytesseract
    print("✅ pytesseract")
except ImportError:
    print("❌ pytesseract - Run: pip install pytesseract")

try:
    from PIL import Image
    print("✅ Pillow")
except ImportError:
    print("❌ Pillow - Run: pip install Pillow")

# Test Tesseract
print()
print("Testing Tesseract-OCR...")
import os
tesseract_path = os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe")
if os.path.exists(tesseract_path):
    print(f"✅ Tesseract found: {tesseract_path}")
else:
    print("❌ Tesseract not found")
    print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   Copy to: Tesseract-OCR folder in this directory")

# Test user-agent module
print()
print("Testing user-agent module...")
try:
    from user_agent import get
    ua = get()
    print(f"✅ user-agent: {ua[:50]}...")
except Exception as e:
    print(f"❌ user-agent: {e}")

print()
print("=" * 50)
print("🎯 NEXT STEPS:")
print("=" * 50)

# Check what's missing
missing = []
try:
    import httpx, bs4, playwright, pytesseract, PIL
    from user_agent import get
except ImportError as e:
    missing.append("Python packages")

if not os.path.exists(tesseract_path):
    missing.append("Tesseract-OCR")

if missing:
    print("❌ Missing components:")
    for item in missing:
        print(f"   - {item}")
    print()
    print("🔧 To fix:")
    if "Python packages" in missing:
        print("   1. Run: pip install -r requirements.txt")
        print("   2. Run: python -m playwright install firefox")
    if "Tesseract-OCR" in missing:
        print("   3. Download and install Tesseract-OCR")
        print("      Run: python download_tesseract.py")
else:
    print("🎉 All dependencies are ready!")
    print()
    print("🚀 You can now run:")
    print("   - python main.py (basic version)")
    print("   - python fast.py (faster version)")

print()
print("=" * 50)
input("Press Enter to exit...")
