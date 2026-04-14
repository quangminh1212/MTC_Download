#!/usr/bin/env python3
"""Test different API endpoints."""
import requests

API_BASE = "https://android.lonoapp.net/api"
USER_AGENT = "Dart/3.0 (dart:io)"

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
})

book_id = 109099

# Test different endpoints
endpoints = [
    f"/books/{book_id}",
    f"/books/{book_id}/chapters",
    f"/books/{book_id}/chapter-list",
    f"/chapters?book_id={book_id}",
    f"/v1/books/{book_id}/chapters",
]

print("Testing API endpoints...")
print("=" * 60)

for endpoint in endpoints:
    url = API_BASE + endpoint
    print(f"\n🔍 Testing: {endpoint}")
    try:
        resp = session.get(url, timeout=10)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ Success! Keys: {list(data.keys())}")
            if 'data' in data:
                if isinstance(data['data'], list):
                    print(f"   📊 Data count: {len(data['data'])}")
                    if len(data['data']) > 0:
                        print(f"   📄 First item keys: {list(data['data'][0].keys())}")
        else:
            print(f"   ❌ Error: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
