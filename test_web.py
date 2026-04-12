#!/usr/bin/env python3
"""Quick web test"""
import requests, re
try:
    r = requests.get('https://lonoapp.net', timeout=5, headers={'User-Agent': 'Chrome/120'})
    print(f"lonoapp.net: {r.status_code}, len={len(r.text)}")
    # Look for API key or config
    keys = re.findall(r'app_key["\s=:]+([A-Za-z0-9+/=:]{20,})', r.text)
    if keys: print(f"Found keys: {keys}")
    # Find JS files
    js = re.findall(r'src="(/[^"]+\.js[^"]*)"', r.text)
    print(f"JS files: {js[:5]}")
except Exception as e:
    print(f"Error: {e}")
