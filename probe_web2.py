#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore metruyencv.com API for content."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import urllib.request
import urllib.error  
import json
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers_web = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
}

def fetch(url):
    print(f"\nGET {url}")
    try:
        req = urllib.request.Request(url, headers=headers_web)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {resp.status}, len={len(data)}")
            return data
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"Error: {e}")
    return None

# metruyencv.com - popular Vietnamese novel site
data = fetch("https://metruyencv.com/truyen/lang-nhan-my-nu-moi-tu-van")
if data:
    # Find chapter list or API
    print(data[:3000])

# Try metruyencv API
apis = [
    "https://metruyencv.com/api/books?slug=lang-nhan-my-nu-moi-tu-van",
    "https://metruyencv.com/api/books/lang-nhan-my-nu-moi-tu-van/chapters",
    "https://metruyencv.com/api/chapters/1",
]
for api in apis:
    data = fetch(api)
    if data:
        print(f"Response: {data[:500]}")

# Try tiemtruyenchu.com
data2 = fetch("https://tiemtruyenchu.com")
if data2:
    # Find API endpoints in JS
    api_refs = re.findall(r'["\']([^"\']*api[^"\']*)["\']', data2)
    print(f"\nAPI refs in tiemtruyenchu: {api_refs[:20]}")
    
    # Find any readable JS with URLs
    script_urls = re.findall(r'https?://[a-zA-Z0-9._/:\-?=&]{10,}', data2)
    unique_urls = set(script_urls)
    print(f"\nURLs in tiemtruyenchu:")
    for u in list(unique_urls)[:30]:
        print(f"  {u}")
