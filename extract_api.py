#!/usr/bin/env python3
"""Extract strings from DEX files to find API endpoints."""
import zipfile
import re
import os

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"

z = zipfile.ZipFile(APK_PATH)

# Read all DEX files and extract readable strings
all_urls = set()
all_api_paths = set()

dex_files = ['classes.dex', 'classes2.dex', 'classes3.dex', 'helper.dex']

for dex in dex_files:
    if dex not in z.namelist():
        continue
    print(f"Processing {dex}...")
    data = z.read(dex)
    
    # Find URLs
    urls = re.findall(rb'https?://[a-zA-Z0-9._/:\-?=&%#@]+', data)
    for u in urls:
        try:
            url = u.decode('utf-8', errors='ignore')
            all_urls.add(url)
        except:
            pass
    
    # Find API path patterns
    api_paths = re.findall(rb'/api/[a-zA-Z0-9._/:\-?=&%#@{}_]+', data)
    for p in api_paths:
        try:
            path = p.decode('utf-8', errors='ignore')
            all_api_paths.add(path)
        except:
            pass

z.close()

print("\n=== ALL URLs FOUND ===")
for url in sorted(all_urls):
    print(f"  {url}")

print(f"\n=== API PATHS FOUND ({len(all_api_paths)}) ===")
for path in sorted(all_api_paths):
    print(f"  {path}")

# Save results
with open(r"C:\Dev\MTC_Download\api_endpoints.txt", 'w', encoding='utf-8') as f:
    f.write("=== URLs ===\n")
    for url in sorted(all_urls):
        f.write(f"{url}\n")
    f.write("\n=== API PATHS ===\n")
    for path in sorted(all_api_paths):
        f.write(f"{path}\n")

print("\nSaved to api_endpoints.txt")
