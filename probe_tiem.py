#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test tiemtruyenchu.com API - find chapter content endpoint.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import urllib.request, urllib.error, json, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'vi-VN,vi',
}

def get(url):
    print(f"\nGET {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {resp.status}, len={len(raw)}")
            return raw
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}")
        body = e.read().decode('utf-8', errors='replace')
        print(body[:300])
    except Exception as e:
        print(f"Error: {e}")
    return None

# Read homepage to find API patterns
home = get("https://tiemtruyenchu.com")
if home:
    # Find JS files
    js_files = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', home)
    print(f"\nJS files: {js_files[:10]}")
    
    # Find story links
    story_links = re.findall(r'href=["\']([^"\']*truyen[^"\']*)["\']', home, re.IGNORECASE)
    print(f"\nStory links: {story_links[:10]}")
    
    # Find any API URLs
    api_urls = re.findall(r'https?://[a-zA-Z0-9._/:\-?=&%#@]{5,}', home)
    print(f"\nURLs in page: {list(set(api_urls))[:20]}")

# Try to find a story list
search_result = get("https://tiemtruyenchu.com/tim-truyen?keyword=lang-nhan")
if search_result:
    print(search_result[:2000])

# Try direct API
apis = [
    "https://tiemtruyenchu.com/api/stories",
    "https://tiemtruyenchu.com/api/books",
    "https://tiemtruyenchu.com/api/chapters",
]
for api in apis:
    get(api)
