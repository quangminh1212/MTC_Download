#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try api.lonoapp.net endpoints and explore additional API routes."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers_mobile = {
    'User-Agent': 'Dart/3.0 (dart:io)',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

def get(url, extra_headers=None):
    h = dict(headers_mobile)
    if extra_headers:
        h.update(extra_headers)
    print(f"\nGET {url}")
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            raw = resp.read().decode('utf-8')
            try:
                data = json.loads(raw)
                print(f"Status: {resp.status}")
                # Check if content is plain text or still encrypted
                if 'data' in data and isinstance(data['data'], dict):
                    ch = data['data']
                    content = ch.get('content', '')
                    if content:
                        print(f"Content type: {'encrypted_b64' if len(content) > 100 and content.replace('=','').replace('+','').replace('/','').isalnum() else 'PLAIN TEXT'}")
                        print(f"Content preview: {content[:200]}")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
            except:
                print(f"Raw: {raw[:500]}")
            return raw
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        try:
            body = e.read().decode('utf-8')
            print(f"Body: {body[:300]}")
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")
    return None

# Try api.lonoapp.net
bases = ['https://api.lonoapp.net', 'https://android.lonoapp.net']

for base in bases:
    print(f"\n{'='*60}")
    print(f"Testing: {base}")
    print('='*60)
    
    # Book list
    get(f"{base}/api/books?per_page=1")
    
    # Chapter with different header
    get(f"{base}/api/chapters/22204525", {
        'X-Platform': 'android',
        'X-App-Version': '1.0.0',
    })

# Try login endpoint to get auth token
print("\n=== Trying login endpoint ===")
login_urls = [
    'https://android.lonoapp.net/api/auth/login',
    'https://android.lonoapp.net/api/login',
    'https://android.lonoapp.net/api/auth',
    'https://api.lonoapp.net/api/auth/login',
]

for url in login_urls:
    print(f"\nPOST {url}")
    try:
        payload = json.dumps({'email': 'test@test.com', 'password': 'test'}).encode()
        req = urllib.request.Request(url, data=payload, headers={
            **headers_mobile,
            'Content-Type': 'application/json',
        }, method='POST')
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print(f"Status: {resp.status}")
            print(resp.read().decode('utf-8')[:500])
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        print(e.read().decode('utf-8')[:300])
    except Exception as e:
        print(f"Error: {e}")
