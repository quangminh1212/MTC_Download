#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Try to brute-force AES key from libapp.so by attempting to decrypt
known chapter content and check if result looks like Vietnamese text.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import zipfile
import base64
import json
import urllib.request
import ssl

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
    print("pycryptodome available")
except ImportError:
    HAS_CRYPTO = False
    print("pycryptodome not available - will install")

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"

# Get fresh encrypted content
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Dart/3.0 (dart:io)',
    'Accept': 'application/json',
}

print("Fetching fresh chapter content...")
req = urllib.request.Request(
    "https://android.lonoapp.net/api/chapters/22204525",
    headers=headers
)
with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    chapter_data = json.loads(resp.read().decode('utf-8'))

content_b64 = chapter_data['data']['content']
print(f"Content b64 length: {len(content_b64)}")

# Parse the encrypted structure
decoded_outer = base64.b64decode(content_b64 + '==')
outer = json.loads(decoded_outer)
iv_b64 = outer['iv']
value_b64 = outer['value']

iv = base64.b64decode(iv_b64 + '==')
ciphertext = base64.b64decode(value_b64 + '==')

print(f"IV ({len(iv)} bytes): {iv.hex()}")
print(f"Ciphertext ({len(ciphertext)} bytes)")

if not HAS_CRYPTO:
    print("\nNeed pycryptodome to decrypt. Run: pip install pycryptodome")
    sys.exit(0)

# Read APK for key search
z = zipfile.ZipFile(APK_PATH)
libapp = z.read('lib/arm64-v8a/libapp.so')
z.close()
print(f"\nlibapp.so: {len(libapp):,} bytes")

def try_decrypt(key, iv, ciphertext):
    """Try to decrypt and check if result is valid Vietnamese text."""
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), 16)
        text = decrypted.decode('utf-8')
        # Vietnamese text check: contains common Vietnamese chars
        viet_chars = 'àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ'
        score = sum(1 for c in text[:200] if c in viet_chars)
        return text[:200], score
    except Exception:
        return None, 0

# Strategy 1: Try common hardcoded keys (known patterns for similar apps)
print("\n=== Strategy: Searching 32-byte high-entropy blocks ===")
import math

def entropy(data):
    if not data:
        return 0
    counts = {}
    for b in data:
        counts[b] = counts.get(b, 0) + 1
    n = len(data)
    return -sum((c/n) * math.log2(c/n) for c in counts.values() if c > 0)

# Slide through libapp.so looking for high-entropy 32-byte blocks
# that decrypt the content to valid UTF-8 Vietnamese
candidates = []
step = 1
best_score = 0
best_key = None
best_text = None

print("Scanning libapp.so for high-entropy 32-byte blocks (this may take a moment)...")
# Only check every 64 bytes to be faster
count = 0
TOTAL = len(libapp) - 32
CHECK_STEP = 16  # check every 16 bytes

for i in range(0, TOTAL, CHECK_STEP):
    key = libapp[i:i+32]
    e = entropy(key)
    if e > 6.5:  # High entropy block
        text, score = try_decrypt(key, iv, ciphertext)
        if score > 0:
            candidates.append((score, i, key.hex(), text))
            if score > best_score:
                best_score = score
                best_key = key
                best_text = text
                print(f"  Found candidate at 0x{i:08x}: score={score}, text={repr(text[:100])}")
    count += 1
    if count % 100000 == 0:
        print(f"  Progress: {i:,}/{TOTAL:,} ({100*i//TOTAL}%)")

print(f"\nTotal candidates: {len(candidates)}")
if candidates:
    candidates.sort(reverse=True)
    print("Top 5 candidates:")
    for score, offset, key_hex, text in candidates[:5]:
        print(f"  Score={score}, offset=0x{offset:08x}, key={key_hex[:16]}...")
        print(f"  Text: {repr(text[:200])}")
else:
    print("No key found in libapp.so")
    print("The key is likely derived from server token after authentication")
