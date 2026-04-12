#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try web sources and alternative content endpoints."""
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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def fetch(url, extra_headers=None):
    h = dict(headers_web)
    if extra_headers:
        h.update(extra_headers)
    print(f"\nGET {url}")
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {resp.status}, len={len(data)}")
            return data
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Try vtruyen.com (linked from book data)
data = fetch("https://vtruyen.com/truyen/lang-nhan-my-nu-moi-tu-van")
if data:
    # Find chapters
    chapters = re.findall(r'href="([^"]*chuong[^"]*)"', data, re.IGNORECASE)
    print(f"Chapter links: {len(chapters)}")
    for c in chapters[:5]:
        print(f"  {c}")

# Try chapter 1 content on vtruyen.com
data2 = fetch("https://vtruyen.com/truyen/lang-nhan-my-nu-moi-tu-van/chuong-1")
if data2:
    # Extract content
    content_match = re.search(r'<div[^>]*class="[^"]*chapter-content[^"]*"[^>]*>(.*?)</div>', data2, re.DOTALL)
    if content_match:
        print(f"Content found: {content_match.group(1)[:500]}")
    print(f"Page size: {len(data2)}")
    # Look for content divs
    divs = re.findall(r'<p[^>]*>(.*?)</p>', data2, re.DOTALL)
    if divs:
        print(f"Paragraphs: {len(divs)}")
        for p in divs[:5]:
            clean = re.sub(r'<[^>]+>', '', p).strip()
            if clean:
                print(f"  {clean[:200]}")

# Check if metruyensangtac.com or tiemtruyenchu.com have the content
sites = [
    ("https://metruyensangtac.com", "metruyensangtac"),
    ("https://tiemtruyenchu.com", "tiemtruyenchu"),
    ("https://metruyencv.com/truyen/lang-nhan-my-nu-moi-tu-van", "metruyencv"),
]

for base, name in sites:
    data = fetch(base)
    if data:
        print(f"\n{name}: site accessible, len={len(data)}")
