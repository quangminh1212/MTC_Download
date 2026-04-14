#!/usr/bin/env python3
"""Kiểm tra chi tiết /init endpoint."""
import requests
import json

url = "https://api.lonoapp.net/api/init"

session = requests.Session()
session.headers.update({
    "User-Agent": "NovelFever/1.0",
    "Accept": "application/json",
})

print("Checking /init endpoint...")
print("=" * 60)

resp = session.get(url, timeout=10)
data = resp.json()

print(json.dumps(data, indent=2, ensure_ascii=False))

# Tìm tất cả keys
def find_all_keys(obj, path="", results=None):
    if results is None:
        results = []
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            results.append((current_path, v))
            find_all_keys(v, current_path, results)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_all_keys(item, f"{path}[{i}]", results)
    
    return results

print("\n" + "=" * 60)
print("All keys and values:")
print("=" * 60)

all_keys = find_all_keys(data)
for path, value in all_keys:
    if isinstance(value, (str, int, float, bool)):
        print(f"{path}: {value}")
