#!/usr/bin/env python3
"""Explore lonoapp.net website"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, re, json

h = {'User-Agent': 'Mozilla/5.0 Chrome/120', 'Accept': '*/*'}
session = requests.Session()
session.headers.update(h)

r = session.get('https://lonoapp.net', timeout=10)
print(f"Home: {r.status_code}, {len(r.text)} bytes")

# Show first 3000 chars
print(r.text[:3000])

# Find all URLs
urls = re.findall(r'https?://[^\s"\'<>]{10,}', r.text)
print(f"\nURLs found:", set(urls))

# Try the chapter endpoint on main domain
resp = session.get('https://lonoapp.net/api/chapters/22204525', timeout=5)
print(f"\n/api/chapters/{22204525}: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    content = data.get('data', {}).get('content', '')
    print(f"Content len: {len(content)}, preview: {content[:100]}")
