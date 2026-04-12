#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe chapter content and try to decrypt."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import urllib.request
import json
import ssl
import base64

BASE_URL = "https://android.lonoapp.net"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL) AppleWebKit/537.36',
    'Accept': 'application/json',
}

def get(path):
    url = BASE_URL + path
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        return json.loads(resp.read().decode('utf-8'))

# Get chapter content
print("=== Chapter 22204525 content ===")
data = get("/api/chapters/22204525")
chapter = data['data']
print(f"Keys: {list(chapter.keys())}")
print(f"name: {chapter['name']}")
print(f"is_locked: {chapter.get('is_locked')}")
print(f"next: {chapter.get('next')}")
print(f"previous: {chapter.get('previous')}")

content_b64 = chapter.get('content', '')
print(f"Content length: {len(content_b64)}")
print(f"Content preview: {content_b64[:200]}")

# Try to decode the content (Base64 -> JSON with iv/value = Laravel encrypted)
try:
    decoded = base64.b64decode(content_b64)
    print(f"\nBase64 decoded ({len(decoded)} bytes):")
    try:
        inner = json.loads(decoded)
        print(f"Inner JSON keys: {list(inner.keys())}")
        for k, v in inner.items():
            val_str = str(v)
            print(f"  {k}: {val_str[:200]}")
    except Exception as e2:
        text = decoded.decode('utf-8', errors='replace')
        print(f"As text: {text[:1000]}")
except Exception as e:
    print(f"Base64 decode failed: {e}")

# Chapters list structure
print("\n=== Chapters list ===")
data3 = get("/api/chapters?filter[book_id]=140643&per_page=5&sort_by=index&sort_dir=asc")
print(f"Keys: {list(data3.keys())}")
print(f"Pagination: {data3.get('pagination')}")
ch_data = data3.get('data', [])
print(f"Count: {len(ch_data)}")
if ch_data:
    print(f"Chapter fields: {list(ch_data[0].keys())}")
    for c in ch_data[:3]:
        print(f"  id={c['id']} index={c['index']} name={c['name']} locked={c.get('is_locked')}")
