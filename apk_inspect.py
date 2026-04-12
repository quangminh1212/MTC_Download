#!/usr/bin/env python3
"""Inspect MTC.apk to find API endpoints and structure."""
import zipfile
import os
import re

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"
EXTRACT_DIR = r"C:\Dev\MTC_Download\apk_extract"

os.makedirs(EXTRACT_DIR, exist_ok=True)

z = zipfile.ZipFile(APK_PATH)
names = z.namelist()
print(f"Total files in APK: {len(names)}")

dex_files = [n for n in names if n.endswith('.dex')]
print(f"DEX files: {dex_files}")

assets = [n for n in names if n.startswith('assets/')]
print(f"Assets ({len(assets)}): {assets[:30]}")

manifests = [n for n in names if 'manifest' in n.lower() or n == 'AndroidManifest.xml']
print(f"Manifest files: {manifests}")

# Extract AndroidManifest.xml (binary XML - need to read as text for URLs)
if 'AndroidManifest.xml' in names:
    data = z.read('AndroidManifest.xml')
    # Extract readable strings from binary XML
    strings = re.findall(rb'[a-zA-Z0-9._/:\-]{10,}', data)
    urls = [s.decode('utf-8', errors='ignore') for s in strings if b'http' in s or b'api' in s.lower() or b'.com' in s]
    print(f"\nURLs/domains in AndroidManifest.xml:")
    for u in urls[:50]:
        print(f"  {u}")

# Check assets for config/api files
print("\n--- Extracting assets ---")
for asset in assets:
    if any(ext in asset.lower() for ext in ['.json', '.xml', '.properties', '.conf', '.yaml', '.txt', '.html']):
        print(f"\n=== {asset} ===")
        try:
            content = z.read(asset).decode('utf-8', errors='ignore')
            print(content[:2000])
        except Exception as e:
            print(f"Error: {e}")

z.close()
print("\nDone!")
