#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse and try to decrypt chapter content."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import urllib.request
import ssl
import json
import base64

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Dart/3.0 (dart:io)', 'Accept': 'application/json'}

req = urllib.request.Request("https://android.lonoapp.net/api/chapters/22204525", headers=headers)
with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    chapter_data = json.loads(resp.read().decode('utf-8'))

content_b64 = chapter_data['data']['content']
print(f"Content b64: {content_b64[:100]}")
print(f"Content b64 len: {len(content_b64)}")

# This is URL-safe base64 possibly
# Try different padding/variants
for variant, b64 in [
    ('standard', content_b64),
    ('url-safe', content_b64.replace('-', '+').replace('_', '/')),
    ('url-decoded', content_b64.replace('%3D', '=').replace('%3d', '=')),
]:
    try:
        s = b64
        # Add padding
        s = s + '=' * (4 - len(s) % 4)
        decoded = base64.b64decode(s)
        print(f"\n{variant}: decoded OK, len={len(decoded)}")
        # Check if valid JSON
        try:
            obj = json.loads(decoded.decode('utf-8', errors='replace'))
            print(f"  JSON keys: {list(obj.keys())}")
            for k, v in obj.items():
                print(f"  {k}: {str(v)[:100]}")
        except:
            print(f"  Not JSON. Raw bytes[:50]: {decoded[:50].hex()}")
            print(f"  As text: {decoded[:200].decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"\n{variant}: FAILED - {e}")
