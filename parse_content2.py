#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast key search - scan libapp.so for AES key using parallel processing."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import zipfile, base64, json, math, ssl, urllib.request
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import multiprocessing as mp

APK_PATH = r"C:\Dev\MTC_Download\MTC.apk"

# Get fresh encrypted content
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Dart/3.0 (dart:io)', 'Accept': 'application/json'}

req = urllib.request.Request("https://android.lonoapp.net/api/chapters/22204525", headers=headers)
with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    chapter_data = json.loads(resp.read().decode('utf-8'))

content_raw = chapter_data['data']['content']

# The content is base64 of a JSON string with binary IV
# Let's decode step by step
import struct

# Decode outer base64
outer_bytes = base64.b64decode(content_raw + '==')
print(f"Outer decoded: {len(outer_bytes)} bytes")
print(f"Starts with: {outer_bytes[:20].hex()}")
print(f"As text: {outer_bytes[:100].decode('utf-8', errors='replace')}")

# It's a JSON string but with binary content in IV
# We need to parse JSON manually
# The JSON has format: {"iv":"...","value":"..."}
# But IV contains binary - need to extract raw bytes

# Try parsing as JSON with latin-1 first
try:
    outer_str = outer_bytes.decode('latin-1')
    print(f"\nLatin-1 decode: {outer_str[:100]}")
    outer_obj = json.loads(outer_str)
    # Now get the binary IV  
    iv_str = outer_obj['iv']
    value_str = outer_obj['value']
    print(f"IV str len: {len(iv_str)}")
    print(f"Value str len: {len(value_str)}")
    
    # The IV in the JSON is base64 of 16 bytes
    # But it seems corrupted because of binary data
    # Try to decode IV as base64
    try:
        iv = base64.b64decode(iv_str + '==')
        print(f"IV ({len(iv)} bytes): {iv.hex()}")
        ciphertext = base64.b64decode(value_str + '==')
        print(f"Ciphertext ({len(ciphertext)} bytes)")
        print(f"Ciphertext[:16]: {ciphertext[:16].hex()}")
    except Exception as e:
        print(f"IV decode error: {e}")
        # IV might be binary - extract bytes directly
        iv_bytes = iv_str.encode('latin-1')
        ciphertext_bytes = base64.b64decode(value_str + '==')
        print(f"IV as bytes ({len(iv_bytes)}): {iv_bytes.hex()}")
        
except Exception as e:
    print(f"Latin-1 parse error: {e}")

# Another approach: look for {"iv" pattern and extract fields
print("\n=== Regex extraction ===")
import re
# Find the JSON structure in outer_bytes
json_match = re.search(rb'"iv":"([^"]+)","value":"([^"]+)"', outer_bytes)
if json_match:
    iv_raw = json_match.group(1)
    val_raw = json_match.group(2)
    print(f"IV raw ({len(iv_raw)}): {iv_raw}")
    print(f"Value raw ({len(val_raw)} chars): {val_raw[:50]}")
    
    # The IV raw is base64 encoded 16 bytes
    try:
        iv = base64.b64decode(iv_raw + b'==')
        print(f"IV decoded ({len(iv)} bytes): {iv.hex()}")
    except Exception as e:
        print(f"IV decode: {e}")
    
    try:
        ciphertext = base64.b64decode(val_raw + b'==')
        print(f"Ciphertext ({len(ciphertext)} bytes)")
    except Exception as e:
        print(f"Ciphertext decode: {e}")
