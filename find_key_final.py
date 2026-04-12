#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final key search - use regex to extract IV and ciphertext properly,
then scan libapp.so for AES-256 key.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import zipfile, base64, json, re, ssl, urllib.request, math, time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"

# Get encrypted content
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

# Parse the encrypted JSON carefully
# Format: {"iv":"<base64-or-raw>","value":"<base64>"}
# Extract using regex on raw bytes
m = re.search(rb'"iv":"([^"]+)","value":"([^"]+)"', outer_bytes)
if not m:
    print("ERROR: Cannot parse encrypted content")
    sys.exit(1)

iv_raw = m.group(1)
val_raw = m.group(2)

print(f"IV raw bytes: {iv_raw.hex()}")
print(f"IV as string: {iv_raw}")

# IV is base64 encoded 16-byte string
# The raw bytes contain the actual IV chars
# Let's try to decode it
try:
    iv = base64.b64decode(iv_raw + b'==')
    print(f"IV decoded ({len(iv)} bytes): {iv.hex()}")
except:
    iv = iv_raw  # Use raw bytes as IV

try:
    ciphertext = base64.b64decode(val_raw + b'==')
    print(f"Ciphertext ({len(ciphertext)} bytes)")
except Exception as e:
    print(f"Cannot decode ciphertext: {e}")
    sys.exit(1)

# The IV from base64 is 20 bytes which is wrong for AES-128-bit IV (16 bytes)
# This means the content might be AES-256 with 128-bit IV = 16 bytes
# But we got 20 bytes... Let's check using first 16 bytes only
iv_16 = iv[:16]
print(f"IV (first 16 bytes): {iv_16.hex()}")

# Now scan libapp.so for key
z = zipfile.ZipFile(APK_PATH)
libapp = z.read('lib/arm64-v8a/libapp.so')
z.close()

VIET_CHARS = set('àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ')

def entropy(data):
    if not data: return 0
    counts = {}
    for b in data:
        counts[b] = counts.get(b, 0) + 1
    n = len(data)
    return -sum((c/n) * math.log2(c/n) for c in counts.values() if c > 0)

def try_decrypt(key_bytes, iv_bytes, ciphertext_bytes):
    try:
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        decrypted = unpad(cipher.decrypt(ciphertext_bytes), 16)
        text = decrypted.decode('utf-8')
        score = sum(1 for c in text[:500] if c in VIET_CHARS)
        return text, score
    except:
        return None, 0

print(f"\nScanning libapp.so ({len(libapp):,} bytes) for AES key...")
print(f"Using IV: {iv_16.hex()}")
print(f"Ciphertext first 16: {ciphertext[:16].hex()}")

best_score = 0
best_key = None
best_text = None

# High-entropy block sizes to try: 16 (AES-128), 24 (AES-192), 32 (AES-256)
KEY_SIZES = [32, 16]

start = time.time()
total = len(libapp) - 32

for i in range(0, total, 8):  # Step 8 bytes
    for key_size in KEY_SIZES:
        if i + key_size > len(libapp):
            continue
        key = libapp[i:i+key_size]
        e = entropy(key)
        if e < 6.0:  # Skip low entropy
            continue
        
        text, score = try_decrypt(key, iv_16, ciphertext)
        if score > 2:  # At least 3 Vietnamese chars
            elapsed = time.time() - start
            print(f"\n[{elapsed:.1f}s] CANDIDATE at 0x{i:08x}: score={score} key={key.hex()}")
            print(f"  Text: {repr(text[:200])}")
            if score > best_score:
                best_score = score
                best_key = key
                best_text = text
    
    if i % 1000000 == 0:
        elapsed = time.time() - start
        pct = 100*i//total
        print(f"Progress: {pct}% ({i:,}/{total:,}) in {elapsed:.1f}s | best_score={best_score}")

print(f"\n\nFINAL RESULT:")
if best_key:
    print(f"KEY FOUND: {best_key.hex()}")
    print(f"Score: {best_score}")
    print(f"Text: {repr(best_text[:500])}")
else:
    print("No key found in libapp.so")
    print("Conclusion: Key is derived from server/token, not hardcoded")
