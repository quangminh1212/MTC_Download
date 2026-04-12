#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: What does auth token contain? Try to decrypt with auth.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, json, re, base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

session = requests.Session()
session.headers.update({
    'User-Agent': 'Dart/3.0 (dart:io)',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
})

BASE = "https://android.lonoapp.net"

# Try login with real or test credentials
# First test with wrong credentials to see field names
resp = session.post(f"{BASE}/api/auth/login", json={
    "email": "test@example.com",
    "password": "wrongpassword",
    "device_name": "Windows",
})
print(f"Login response: {resp.status_code}")
print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

# Try register with valid email
resp2 = session.post(f"{BASE}/api/auth/register", json={
    "name": "User Test",
    "email": "uniquetest9999@gmail.com",
    "password": "Test@123456",
    "password_confirmation": "Test@123456",
    "device_name": "Windows",
})
print(f"\nRegister response: {resp2.status_code}")
data = resp2.json()
print(json.dumps(data, ensure_ascii=False, indent=2))

# If register success, check if there's an auth key
if data.get('success') and data.get('data'):
    print("\n=== TOKEN FOUND ===")
    auth_data = data['data']
    print(f"Auth data keys: {list(auth_data.keys())}")
    token = auth_data.get('token') or auth_data.get('access_token') or auth_data.get('api_token')
    if token:
        print(f"Token: {token[:50]}...")
        
        # Try getting chapter with token
        session.headers['Authorization'] = f'Bearer {token}'
        ch_resp = session.get(f"{BASE}/api/chapters/22204525")
        ch_data = ch_resp.json()['data']
        content = ch_data.get('content', '')
        print(f"\nContent with token (len={len(content)}): {content[:100]}")
        
        # Check if content is different (unencrypted)
        outer = base64.b64decode(content + '==')
        print(f"Decoded: {outer[:100].decode('utf-8', errors='replace')}")
        
        # Check if key is in response
        if 'key' in auth_data:
            print(f"\nEncryption key found: {auth_data['key']}")
        if 'secret' in auth_data:
            print(f"\nSecret found: {auth_data['secret']}")
