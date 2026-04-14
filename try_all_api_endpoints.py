#!/usr/bin/env python3
"""Thử tất cả các API endpoints có thể để tìm config hoặc key."""
import requests
import json

# Tất cả các API base URLs tìm được
api_bases = [
    "https://api.lonoapp.net/api",
    "https://android.lonoapp.net/api",
    "https://api.lonoapp.net",
    "https://android.lonoapp.net",
]

# Các endpoints có thể chứa config/key
config_endpoints = [
    "/config",
    "/app/config",
    "/settings",
    "/app/settings",
    "/encryption/key",
    "/app/key",
    "/version",
    "/app/version",
    "/init",
    "/app/init",
    "/bootstrap",
    "/app/bootstrap",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "NovelFever/1.0",
    "Accept": "application/json",
})

print("Trying all possible API endpoints...")
print("=" * 60)

found_configs = []

for base in api_bases:
    print(f"\n🔍 Testing base: {base}")
    print("-" * 60)
    
    for endpoint in config_endpoints:
        url = base + endpoint
        try:
            resp = session.get(url, timeout=5)
            
            if resp.status_code == 200:
                print(f"  ✅ {endpoint} - Status: {resp.status_code}")
                
                try:
                    data = resp.json()
                    print(f"     Response: {json.dumps(data, indent=2)[:200]}...")
                    
                    # Tìm key trong response
                    def find_keys(obj, path=""):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if 'key' in k.lower() or 'secret' in k.lower():
                                    print(f"     🔑 Found: {path}.{k} = {v}")
                                    found_configs.append({
                                        'url': url,
                                        'key': k,
                                        'value': v
                                    })
                                find_keys(v, f"{path}.{k}")
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                find_keys(item, f"{path}[{i}]")
                    
                    find_keys(data)
                    
                except:
                    print(f"     Response (text): {resp.text[:200]}...")
                    
            elif resp.status_code == 404:
                pass  # Skip 404
            else:
                print(f"  ⚠️  {endpoint} - Status: {resp.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️  {endpoint} - Timeout")
        except Exception as e:
            pass  # Skip errors

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if found_configs:
    print(f"\n✅ Found {len(found_configs)} potential keys:")
    for config in found_configs:
        print(f"\nURL: {config['url']}")
        print(f"Key: {config['key']}")
        print(f"Value: {config['value']}")
else:
    print("\n❌ No config endpoints found")
    print("\nTrying alternative approach...")
