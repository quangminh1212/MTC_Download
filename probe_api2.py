#!/usr/bin/env python3
"""Probe more API endpoints with real book IDs."""
import urllib.request
import json
import ssl
from urllib.parse import urlencode, quote

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
    print(f"\nGET {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            print(f"Status: {resp.status}")
            try:
                j = json.loads(data)
                print(json.dumps(j, ensure_ascii=False, indent=2)[:3000])
            except:
                print(data[:2000])
            return data
    except Exception as e:
        print(f"Error: {e}")
        return None

# Get first book to understand structure
print("=== Getting books list ===")
data = get("/api/books?per_page=2")
if data:
    j = json.loads(data)
    if 'data' in j and j['data']:
        book = j['data'][0]
        book_id = book['id']
        slug = book['slug']
        first_ch = book.get('first_chapter')
        print(f"\nFirst book: id={book_id}, slug={slug}, first_chapter={first_ch}")
        print(f"Book keys: {list(book.keys())}")
        
        # Try various chapter endpoints
        endpoints_to_try = [
            f"/api/chapters?filter%5Bbook_id%5D={book_id}",
            f"/api/chapters?filter[book_id]={book_id}",
            f"/api/chapters?book_id={book_id}",
            f"/api/books/{book_id}/chapters",
            f"/api/books/{slug}",
            f"/api/books?slug={slug}",
            f"/api/books?filter[slug]={slug}",
            f"/api/chapters/{first_ch}",
        ]
        
        for ep in endpoints_to_try:
            get(ep)
            print("-" * 60)

# Check pagination
print("\n=== Checking pagination structure ===")
data2 = get("/api/books?per_page=1")
if data2:
    j2 = json.loads(data2)
    print(f"Top-level keys: {list(j2.keys())}")
    if 'meta' in j2:
        print(f"Meta: {j2['meta']}")
    if 'links' in j2:
        print(f"Links: {j2['links']}")
