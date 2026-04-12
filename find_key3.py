#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search libapp.so for decrypt key patterns near encryption function names."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import zipfile
import re
import struct

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"
z = zipfile.ZipFile(APK_PATH)

data = z.read('lib/arm64-v8a/libapp.so')
z.close()

print(f"libapp.so size: {len(data):,}")

# Find all ASCII printable strings >= 10 chars
def extract_strings(data, min_len=10):
    results = []
    current = bytearray()
    for i, b in enumerate(data):
        if 0x20 <= b <= 0x7e:
            current.append(b)
        else:
            if len(current) >= min_len:
                results.append((i - len(current), bytes(current).decode('ascii', errors='ignore')))
            current = bytearray()
    return results

print("Extracting strings...")
all_strings = extract_strings(data, min_len=8)
print(f"Total strings: {len(all_strings)}")

# Find strings containing crypto keywords
crypto_keywords = ['encrypt', 'decrypt', 'AES', 'CBC', 'key', 'iv', 'cipher', 'secret', 'token', 'salt', 'hash']
crypto_strings = [(offset, s) for offset, s in all_strings 
                  if any(kw.lower() in s.lower() for kw in crypto_keywords)
                  and not s.startswith('package:') 
                  and not s.startswith('dev.')
                  and 'flutter' not in s.lower()
                  and 'android' not in s.lower()
                  and len(s) > 15]

print(f"\nCrypto-related strings ({len(crypto_strings)}):")
for offset, s in crypto_strings[:50]:
    print(f"  0x{offset:08x}: {repr(s)}")

# Specifically find base64 strings that look like keys
b64_pattern = re.compile(rb'[A-Za-z0-9+/]{32,64}={0,2}')
b64_matches = b64_pattern.findall(data)
print(f"\nPotential base64 keys ({len(b64_matches)} found, sample):")
for m in b64_matches[:30]:
    s = m.decode('ascii', errors='ignore')
    # Filter to likely keys (length 32, 44, 64)
    if len(s) in [32, 43, 44, 64]:
        print(f"  len={len(s)}: {s}")

# Find the API base URL strings and nearby constants
print("\n=== Strings near 'android.lonoapp.net' ===")
lono_pos = data.find(b'android.lonoapp.net')
if lono_pos >= 0:
    context = data[max(0, lono_pos-200):lono_pos+500]
    strings_nearby = extract_strings(context, min_len=5)
    for _, s in strings_nearby:
        print(f"  {repr(s)}")

# Find decryption function parameters 
print("\n=== All strings with 'lonoapp' ===")
lono_strings = [(o, s) for o, s in all_strings if 'lonoapp' in s.lower() or 'lono' in s.lower()]
for o, s in lono_strings:
    print(f"  0x{o:08x}: {repr(s)}")
