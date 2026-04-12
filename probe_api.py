#!/usr/bin/env python3
"""Probe lonoapp.net API to understand structure."""
import urllib.request
import json
import ssl

BASE_URL = "https://android.lonoapp.net"

# Disable SSL verification for testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL) AppleWebKit/537.36',
    'Accept': 'application/json',
    'X-Requested-With': 'com.lonoapp.android',
}

def get(path):
    url = BASE_URL + path
    print(f"\nGET {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {resp.status}")
            print(f"Response ({len(data)} chars): {data[:2000]}")
            return data
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test various endpoints
endpoints = [
    "/api/books",
    "/api/books?page=1",
    "/api/chapters",
    "/api/chapters/1",
    "/api/chapters?filter[book_id]=1",
    "/api/genres",
    "/api/genres/",
    "/api/",
    "/api/categories",
    "/api/stories",
    "/api/stories/1",
    "/api/books/1",
    "/api/books/1/chapters",
]

for ep in endpoints:
    get(ep)
    print("-" * 60)
