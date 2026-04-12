#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search libapp.so for hardcoded keys and API URLs."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import zipfile
import re

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"
z = zipfile.ZipFile(APK_PATH)

# List all lib files
lib_files = [n for n in z.namelist() if n.startswith('lib/')]
print(f"Lib files: {lib_files[:20]}")

# Focus on arm64 libapp.so (flutter compiled dart)
target_libs = [n for n in lib_files if 'libapp.so' in n or 'libflutter.so' in n]
print(f"Flutter libs: {target_libs}")

for libname in target_libs:
    print(f"\n=== {libname} ===")
    data = z.read(libname)
    print(f"Size: {len(data):,} bytes")
    
    # Search for API URLs
    urls = re.findall(rb'https?://[a-zA-Z0-9._/:\-?=&%#@]{10,}', data)
    lono_urls = set()
    for u in urls:
        url = u.decode('ascii', errors='ignore')
        if 'lonoapp' in url or 'android' in url:
            lono_urls.add(url)
    if lono_urls:
        print(f"Lonoapp URLs:")
        for u in lono_urls:
            print(f"  {u}")
    
    # Search for all URLs
    all_urls = set(u.decode('ascii', errors='ignore') for u in urls)
    interesting = [u for u in all_urls if any(x in u for x in ['api', 'lono', 'metruyencv', 'truyen', 'novel'])]
    if interesting:
        print(f"Interesting URLs:")
        for u in interesting[:20]:
            print(f"  {u}")
    
    # Search for AES key patterns (32 bytes = 64 hex chars or 44 base64 chars)
    # Laravel APP_KEY format: base64:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    b64_keys = re.findall(rb'base64:[A-Za-z0-9+/]{43}=', data)
    if b64_keys:
        print(f"Laravel base64 keys:")
        for k in b64_keys[:10]:
            print(f"  {k.decode('ascii')}")
    
    # Find AES key in nearby context 
    aes_patterns = re.findall(rb'.{0,50}AES.{0,50}', data)
    interesting_aes = [p for p in aes_patterns if any(c.isalpha() for c in p.decode('ascii', errors='ignore').split('AES')[-1][:10])]
    
    # Search for readable long strings (config values)
    # Find strings between quotes > 20 chars
    strings = re.findall(rb'[\x20-\x7e]{20,500}', data)
    config_strings = []
    for s in strings:
        text = s.decode('ascii', errors='ignore').strip()
        if any(kw in text.lower() for kw in ['android', 'api', 'base_url', 'encrypt', 'secret', 'key', 'token', 'lono']):
            config_strings.append(text)
    if config_strings:
        print(f"Config strings:")
        for s in config_strings[:30]:
            print(f"  {repr(s[:200])}")

z.close()
print("\nDone!")
