#!/bin/bash
# Quick Start Guide for MTC_Download

echo "================================"
echo "MTC Novel Downloader - Quick Start"
echo "================================"
echo ""

# Check if key exists
if [ -f "WORKING_KEY.txt" ] || [ -f "APP_KEY.txt" ]; then
    echo "✅ Encryption key found!"
    echo ""
    echo "Usage:"
    echo "  python download_and_decrypt.py \"Tên Truyện\""
    echo ""
else
    echo "⚠️  No encryption key found!"
    echo ""
    echo "Content will be encrypted. To find the key:"
    echo ""
    echo "Method 1 (Recommended): mitmproxy"
    echo "  pip install mitmproxy"
    echo "  mitmweb --listen-port 8080"
    echo "  Configure BlueStacks proxy: 127.0.0.1:8080"
    echo "  Install cert from http://mitm.it"
    echo "  Run app and capture traffic"
    echo ""
    echo "Method 2: Frida"
    echo "  pip install frida-tools"
    echo "  frida -U -f com.lonoapp.mtc -l hook_decrypt.js"
    echo ""
    echo "See HUONG_DAN_TIM_KEY.md for detailed instructions"
    echo ""
fi

echo "Available commands:"
echo "  python download_and_decrypt.py \"Book Name\"     - Download with auto-decrypt"
echo "  python download_to_extract.py \"Book Name\"      - Download to extract/novels/"
echo "  python test_decrypt_with_key.py \"base64:KEY\"   - Test a specific key"
echo ""
echo "Documentation:"
echo "  README.md              - Main documentation"
echo "  HUONG_DAN_TIM_KEY.md   - Key finding guide"
echo "  TONG_KET.md            - Project summary"
echo ""
