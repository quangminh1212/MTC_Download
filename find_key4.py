#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find AES key by trying to decrypt known chapter with candidate keys."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import zipfile
import re
import base64
import json
import struct

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"
z = zipfile.ZipFile(APK_PATH)
data = z.read('lib/arm64-v8a/libapp.so')
z.close()

# Known encrypted content (from chapter 22204525)
# Let's get a fresh one - the iv+value from our last request
ENCRYPTED_B64 = "eyJpdiI6InVnQ3E5NvoIWAEaNLZ4vp1y6EJ3QUpKc0cxL25NUERjVXc9PSIsInZhbHVlIjoicjJDWnl3cnh5N3BoeWI2M0ZBVlZtbW1tQ1RXSU1sL3lhb21RSFJEMjA3azZNMGhHdzhhc0NIbWRCMzlJb29HVXFRMDR5OVV3MlQxb3d2aE5pa0Jra3gxRkZrb0h2MnBLbnpucFV3WFJaMHBtYVpxYW9YM2kzRlFLeVNSTGxCSXZYNXNGcXpYck1ZYjhzY3E1akQyUVBmSW1oNjdmMU9DQjJDYWxNbkpFcmI3M2RUYlhTcm9SSkhCTEliOU84YTVpMVc5aHRVbXAzeHFYYnBzaWkvTTYzOHJiV2FBOUI0a1ZoYzJ3VFBOVnN1WEloNCtHb1hHc0gxQUxKd0lDeXpUdWQxeVlYSU5Ob2ZnR0dkNkpNaDhlOXFQQ2pQN3BTM09KVlQzNE1TNkZsMG5oMW5Bc0NUNFI2emVlUDlCZHZIRWJyd01tUjU0OFZhRzVORElCbHg5WkpSMzE0WXBHSEFtU3JWSW0wM09UeEZ1WVl4UXpxb0FkVVlxSFFFNzNWMjBCTm9vbFNaQ21jalo2TDdiRW55MDJsSnlIbkpZV09MUXZIL3Y3M2ZrUGhTcE9KMWQ3dnpXZ3d4Z1c0OGU2OGNpbzFuVFl6N2RSb2w4STNkOGdPY1FXMzBvY3lMZkJCaHVuWVBJWVdYZm50ekh4U0d6OUh3b09rQ1M3dGRSbkVwZDlDWnpIT2xJYkdDSkovdU5Va2VaeUFBcEpSRWh3bmhJZHJsaGMxZEtMQlMyZ2VJeXZOU3V3dVZBTFhLOUpsMzJGcFBqMlRLbkNkLzlsVFBuTU1sZzBhcllPaVFyb1ZjeGYvczZSaE1xVGU0RGh4R0dVdERHbFlhWkxhMVdyMXJ5MEFjZ0VQc0wrdFozVTNvbTF4MkxMN3N5QXJNVm5sNDZTODhOVktlSXljdCtscHgzemNaMkF1aFpjd0R5QTduaUd3eHROcS8zOXhvaHQ0WXFFREFSNGFxMEo2SmM5YnZKbmZ4U2ZoZW0zd0ZCRTlUYTg4a1Nab3cxSmhHL2I0cTMyWW5YK0hCVzQzK0RJY2lFbXFiNEJEMWYwaEFKY21XL1lqOFd0R3pHSzNHZFNXWkx1Yzg4Vmh3JTNEJTNEIn0="

try:
    decoded_outer = base64.b64decode(ENCRYPTED_B64 + '==')
    outer_json = json.loads(decoded_outer)
    iv_b64 = outer_json['iv']
    value_b64 = outer_json['value']
    print(f"IV (b64): {iv_b64}")
    print(f"Value len: {len(value_b64)}")
    
    iv_bytes = base64.b64decode(iv_b64)
    value_bytes = base64.b64decode(value_b64)
    print(f"IV ({len(iv_bytes)} bytes): {iv_bytes.hex()}")
    print(f"Ciphertext ({len(value_bytes)} bytes)")
except Exception as e:
    print(f"Parse error: {e}")

# Try to find 32-byte blocks in libapp.so that could be AES-256 key
# Strategy: Look for sequences of 32 bytes where entropy is "key-like" (high entropy)
print("\n=== Searching for potential 32-byte AES keys ===")

# Method 1: Find null-terminated strings of exactly 32 printable chars  
print("\nMethod 1: 32-char printable strings")
matches = re.findall(rb'[\x20-\x7e]{32}\x00', data)
for m in matches[:30]:
    s = m[:-1].decode('ascii', errors='ignore')
    # Skip common Flutter/Dart noise
    if not any(kw in s for kw in ['flutter', 'dart', 'android', 'class', 'package', 'method', 'return', 'function']):
        print(f"  {repr(s)}")

# Method 2: Look for base64 encoded 32-byte key (= 44 chars base64)
print("\nMethod 2: base64 keys (44 chars)")
b64_44 = re.findall(rb'[A-Za-z0-9+/]{43}=', data)
for m in b64_44[:50]:
    s = m.decode('ascii', errors='ignore')
    # Decode and check if it's 32 bytes (AES-256 key size)
    try:
        decoded = base64.b64decode(s)
        if len(decoded) == 32:
            print(f"  {s} -> {decoded.hex()}")
    except:
        pass

# Method 3: Look for hex-encoded 32-byte key (64 hex chars)
print("\nMethod 3: hex-encoded 32-byte keys")
hex_64 = re.findall(rb'[0-9a-f]{64}', data)
for m in hex_64[:20]:
    s = m.decode('ascii', errors='ignore')
    # Check entropy
    unique_chars = len(set(m))
    if unique_chars > 10:  # High entropy
        print(f"  {s}")
