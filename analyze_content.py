#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if content is decryptable by looking at the content structure carefully.
The Dart encrypt package uses: Encrypter(AES(key)).encrypt(text, iv: iv)
Key is typically Key.fromBase64('...') or Key.fromUtf8('...')
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import zipfile, re, base64, json, ssl, urllib.request
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"

# Get fresh encrypted content  
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request(
    "https://android.lonoapp.net/api/chapters/22204525",
    headers={'User-Agent': 'Dart/3.0 (dart:io)', 'Accept': 'application/json'}
)
with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    chapter_data = json.loads(resp.read().decode('utf-8'))

content_b64 = chapter_data['data']['content']
outer_bytes = base64.b64decode(content_b64 + '==')

# Extract iv and value using regex on raw bytes
m = re.search(rb'"iv":"([^"]+)","value":"([^"]+)"', outer_bytes)
if not m:
    print("Cannot parse encrypted content")
    exit(1)

iv_raw = m.group(1)  # raw bytes of IV string from JSON
val_raw = m.group(2) # raw bytes of ciphertext base64

print(f"IV raw ({len(iv_raw)} bytes): {iv_raw}")
print(f"Val raw ({len(val_raw)} bytes): {val_raw[:50]}")

# The Dart encrypt package stores IV as base64 string in Flutter
# But the server-side Laravel stores it with possible binary
# Let's analyze the IV more carefully

# Try: IV is NOT base64 but raw bytes from the JSON string field
# The JSON encoding would represent binary with escape sequences
# But since we see printable + binary, it's the raw bytes after JSON parsing

# Option 1: IV raw bytes directly (already 36 bytes... not 16)
# Option 2: IV is the base64 string that when decoded gives 16 bytes

# Let's count: "pBr1vn}JEG\x96mK\xd5\xb4\xea\x91\x10GGd4+ts+fhcI4dzQ=="
# The == at end suggests it IS base64
# Decode: pBr1vn}JEG... but } is not in standard base64!

# Aha! The IV in the JSON contains non-base64 chars because it has binary bytes
# that were JSON-encoded wrongly. The Dart encrypt package stores IV as:
# base64-encoded 16 bytes = 24 chars (with padding)

# Let me check: if IV is 24-char base64 = 16 bytes
print(f"\nParsing binary IV:")
# Find the clean base64 part (remove non-base64 chars from IV)
iv_ascii_only = re.sub(rb'[^A-Za-z0-9+/=]', b'', iv_raw)
print(f"IV ascii-only ({len(iv_ascii_only)}): {iv_ascii_only}")
try:
    iv_decoded = base64.b64decode(iv_ascii_only + b'==')
    print(f"IV decoded ({len(iv_decoded)} bytes): {iv_decoded.hex()}")
except Exception as e:
    print(f"IV decode error: {e}")

# The real IV might be the full raw bytes of the JSON IV field
# Dart's encrypt package might store IV differently
# Let's check the Dart encrypt package source

# Actually, in Dart encrypt package:
# final encrypted = encrypter.encrypt(text, iv: iv);
# encrypted.base64 returns base64 of: iv_bytes + ciphertext_bytes (16+N bytes)
# And saved as JSON: {"iv": base64(iv), "value": base64(cipher)}

# BUT the issue is that the "iv" field contains BINARY bytes because
# the IV was NOT base64 encoded before storing in JSON!

# So the actual IV is in the raw JSON bytes, not as base64
# The JSON string "iv":"..." contains the 16 raw IV bytes as-is

# Let me try: use the first 16 raw bytes of iv_raw as IV
# (since iv_raw could be 16 raw bytes represented with JSON escaping)
if len(iv_raw) >= 16:
    # Try RAW bytes as IV (not base64)
    iv_candidate = iv_raw[:16]
    print(f"\nTrying raw first-16-bytes as IV: {iv_candidate.hex()}")
    
    try:
        ciphertext = base64.b64decode(val_raw + b'==')
        
        # Load APK to get candidate key
        z = zipfile.ZipFile(APK_PATH)
        libapp = z.read('lib/arm64-v8a/libapp.so')
        z.close()
        
        # Try some UTF-8 key strings that might be hardcoded
        candidate_keys = [
            b'1234567890123456',  # 16-byte test
            b'12345678901234567890123456789012',  # 32-byte test
            b'metruyencv_secret',
            b'lonoapp_secret_k',
            b'lonoapp_aes_key_',
        ]
        
        for key in candidate_keys:
            # Pad to 32 bytes
            key32 = (key + b'\x00' * 32)[:32]
            try:
                cipher = AES.new(key32, AES.MODE_CBC, iv_candidate)
                decrypted = unpad(cipher.decrypt(ciphertext), 16)
                text = decrypted.decode('utf-8', errors='replace')
                viet = sum(1 for c in text[:200] if c in 'àáảãạăắặâấậđèẹêếệìíọôốộơớờợùúụưứừựỳý')
                print(f"  Key {key[:8]!r}... -> viet_score={viet}, text={repr(text[:100])}")
            except Exception as e:
                pass  # Decryption failed (wrong key)
    except Exception as e:
        print(f"Error: {e}")

# Check the ciphertext length to understand block size
print(f"\nCiphertext info:")
try:
    ciphertext = base64.b64decode(val_raw + b'==')
    print(f"Length: {len(ciphertext)} bytes = {len(ciphertext)/16} AES blocks (16-byte)")
    print(f"First block: {ciphertext[:16].hex()}")
    print(f"Last block: {ciphertext[-16:].hex()}")
    # AES-CBC: last block tells us the padding
    # Padding value = last byte of last block (but only after decryption)
    print(f"Word count for chapter: {chapter_data['data']['word_count']}")
    print(f"Expected text size: ~{chapter_data['data']['word_count'] * 3} bytes (avg 3 bytes/word Vietnamese)")
except Exception as e:
    print(f"Error: {e}")
