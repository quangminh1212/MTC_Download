#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test various headers to get plain-text content from API.
Also check if there's a web version of lonoapp.net
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, json, base64, re

session = requests.Session()
BASE = "https://android.lonoapp.net"

def test_chapter(chapter_id, headers_extra=None):
    headers = {'User-Agent': 'Dart/3.0 (dart:io)', 'Accept': 'application/json'}
    if headers_extra:
        headers.update(headers_extra)
    resp = requests.get(f"{BASE}/api/chapters/{chapter_id}", headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()['data']
        content = data.get('content', '')
        is_enc = len(content) > 50 and not any(c in content[:100] for c in 'àáảãạăđèéẻẽ')
        print(f"  Content len={len(content)}, encrypted={is_enc}, headers={list(headers_extra.keys()) if headers_extra else []}")
        if not is_enc:
            print(f"  ** PLAIN TEXT: {content[:300]}")
        return not is_enc
    print(f"  Error: {resp.status_code}")
    return False

print("=== Testing various request headers ===")
test_chapter(22204525)
test_chapter(22204525, {'X-Platform': 'web'})
test_chapter(22204525, {'X-App-Type': 'web'})
test_chapter(22204525, {'X-No-Encrypt': '1'})
test_chapter(22204525, {'X-Client': 'web'})
test_chapter(22204525, {'Accept': 'text/plain'})
test_chapter(22204525, {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'})

# Try web version of lonoapp
print("\n=== Testing web API endpoints ===")
web_bases = [
    "https://lonoapp.net",
    "https://www.lonoapp.net",
    "https://web.lonoapp.net",
]
for wb in web_bases:
    try:
        resp = requests.get(f"{wb}/api/chapters/22204525", timeout=5)
        print(f"GET {wb}/api/chapters/22204525: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('data', {}).get('content', '')
            print(f"  Content len={len(content)}, preview={content[:100]}")
    except Exception as e:
        print(f"GET {wb}: {type(e).__name__}")

# Check if there's an unencrypted field or a different endpoint
print("\n=== Check chapter extra fields ===")
resp = requests.get(f"{BASE}/api/chapters/22204525", 
    headers={'User-Agent': 'Dart/3.0 (dart:io)', 'Accept': 'application/json'},
    timeout=10)
data = resp.json()['data']
for key, val in data.items():
    if key != 'content':
        print(f"  {key}: {str(val)[:100]}")

# Check books list for web content URL
print("\n=== Check book links ===")
resp2 = requests.get(f"{BASE}/api/books", params={"per_page": 3},
    headers={'User-Agent': 'Dart/3.0 (dart:io)', 'Accept': 'application/json'},
    timeout=10)
books = resp2.json()['data'][:2]
for book in books:
    link = book.get('link', '')
    print(f"  Book '{book['name'][:30]}' -> link: {link}")
    # Try fetching the web link to get unencrypted content
    if link and 'http' in link:
        try:
            wr = requests.get(link, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 Chrome',
            })
            print(f"    Web: {wr.status_code}, len={len(wr.text)}")
        except Exception as e:
            print(f"    Web error: {e}")
