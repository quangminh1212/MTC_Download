#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try login and check if auth changes content format."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = "https://android.lonoapp.net"

headers = {
    'User-Agent': 'Dart/3.0 (dart:io)',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

def post(path, body):
    url = BASE + path
    payload = json.dumps(body).encode()
    print(f"\nPOST {url}")
    print(f"Body: {body}")
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read().decode('utf-8')
            print(f"Status: {resp.status}")
            try:
                print(json.dumps(json.loads(data), ensure_ascii=False, indent=2)[:2000])
            except:
                print(data[:1000])
            return data
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        try:
            body_r = e.read().decode('utf-8')
            print(json.dumps(json.loads(body_r), ensure_ascii=False, indent=2)[:1000])
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")
    return None

# Try login with various payloads to understand required fields
post("/api/auth/login", {
    "email": "test@gmail.com",
    "password": "password123",
    "device_name": "Android"
})

post("/api/auth/login", {
    "email": "admin@lonoapp.net",
    "password": "admin",
    "device_name": "HUAWEI P30 Pro"
})

# Try register
post("/api/auth/register", {
    "name": "TestUser",
    "email": "testuser12345@test.com",
    "password": "Test@12345",
    "password_confirmation": "Test@12345",
    "device_name": "Android"
})

# Social login info
print("\n=== Testing social/guest login ===")
post("/api/auth/guest", {
    "device_name": "Android",
    "device_id": "abc123"
})

post("/api/auth/social", {
    "provider": "google",
    "access_token": "test",
    "device_name": "Android"
})

# Also check if chapter content differs based on any request param
import urllib.request as ur

def get_chapter_with_key(chapter_id, key_header=None):
    url = f"{BASE}/api/chapters/{chapter_id}"
    h = dict(headers)
    if key_header:
        h.update(key_header)
    h.pop('Content-Type', None)
    req = ur.Request(url, headers=h)
    print(f"\nGET {url} {key_header}")
    try:
        with ur.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content = data.get('data', {}).get('content', '')
            print(f"Content len: {len(content)}, prefix: {content[:80]}")
    except Exception as e:
        print(f"Error: {e}")

get_chapter_with_key(22204525)
get_chapter_with_key(22204525, {'X-Decrypt': '1'})
get_chapter_with_key(22204525, {'Accept': 'text/plain'})
