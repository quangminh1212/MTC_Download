#!/usr/bin/env python3
"""Kiểm tra format của encrypted content."""
import base64
import json

# Read encrypted content
with open("extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt", 'r', encoding='utf-8') as f:
    lines = f.readlines()
    encrypted = lines[2].strip()

print("Encrypted content (first 200 chars):")
print(encrypted[:200])
print(f"\nLength: {len(encrypted)}")

# Try to decode
try:
    decoded = base64.b64decode(encrypted)
    print(f"\n✅ Base64 decoded successfully")
    print(f"Decoded length: {len(decoded)}")
    print(f"First 100 bytes: {decoded[:100]}")
    
    # Try to parse as JSON
    try:
        data = json.loads(decoded)
        print(f"\n✅ JSON parsed successfully")
        print(f"Keys: {list(data.keys())}")
        
        if 'iv' in data:
            print(f"\nIV: {data['iv'][:50]}...")
            print(f"IV length: {len(data['iv'])}")
            
            # Try to decode IV
            try:
                iv_bytes = base64.b64decode(data['iv'])
                print(f"✅ IV decoded: {len(iv_bytes)} bytes")
            except Exception as e:
                print(f"❌ IV decode failed: {e}")
        
        if 'value' in data:
            print(f"\nValue length: {len(data['value'])}")
            try:
                value_bytes = base64.b64decode(data['value'])
                print(f"✅ Value decoded: {len(value_bytes)} bytes")
            except Exception as e:
                print(f"❌ Value decode failed: {e}")
        
        if 'mac' in data:
            print(f"\nMAC: {data['mac'][:50]}...")
            print(f"MAC length: {len(data['mac'])}")
            
    except Exception as e:
        print(f"\n❌ JSON parse failed: {e}")
        print(f"Decoded content (first 200 chars): {decoded[:200]}")
        
except Exception as e:
    print(f"\n❌ Base64 decode failed: {e}")
