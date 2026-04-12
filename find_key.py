#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find encryption keys in APK - search flutter assets and all text files."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import zipfile
import re

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"
z = zipfile.ZipFile(APK_PATH)

# Search in flutter kernel/snapshot for encryption keys
flutter_files = [
    'assets/flutter_assets/kernel_blob.bin',
    'assets/flutter_assets/isolate_snapshot_data',
    'assets/flutter_assets/vm_snapshot_data',
]

print("=== Searching flutter binary assets for keys/URLs ===")
for fname in flutter_files:
    if fname not in z.namelist():
        print(f"Not found: {fname}")
        continue
    
    print(f"\nSearching {fname}...")
    data = z.read(fname)
    
    # Find base64-looking strings (potential keys)
    # AES-256-CBC key base64 = 44 chars
    keys_b64 = re.findall(rb'[A-Za-z0-9+/]{43}=', data)
    if keys_b64:
        print(f"  Potential base64 keys:")
        for k in keys_b64[:20]:
            print(f"    {k.decode('ascii', errors='ignore')}")
    
    # Find URLs
    urls = re.findall(rb'https?://[a-zA-Z0-9._/:\-?=&%#@]+', data)
    if urls:
        print(f"  URLs found:")
        for u in set(urls):
            try:
                url = u.decode('ascii', errors='ignore')
                if 'lonoapp' in url or 'android' in url.lower():
                    print(f"    {url}")
            except:
                pass
    
    # Find lonoapp references
    lono = re.findall(rb'lono[a-zA-Z0-9._/:\-?=&%#@]{3,}', data)
    for l in lono[:20]:
        print(f"  lonoapp ref: {l.decode('ascii', errors='replace')}")

# Also search all DEX files for AES keys
print("\n=== Searching DEX files for AES/encryption patterns ===")
dex_files = ['classes.dex', 'classes2.dex', 'classes3.dex']
for dex in dex_files:
    if dex not in z.namelist():
        continue
    data = z.read(dex)
    
    # Search for "decrypt", "encrypt", "AES", "key" near readable strings
    patterns = [
        rb'AES[/A-Za-z-]{0,20}',
        rb'base64_[a-z]+',
        rb'APP_KEY[^a-z]{0,5}[A-Za-z0-9+/=]{20,}',
        rb'secret[^a-z]{0,5}[A-Za-z0-9+/=]{20,}',
    ]
    for p in patterns:
        matches = re.findall(p, data, re.IGNORECASE)
        if matches:
            print(f"  In {dex}, pattern '{p}': {[m.decode('ascii', errors='ignore') for m in matches[:5]]}")

z.close()
print("\nDone!")
