#!/usr/bin/env python3
"""Phân tích cấu trúc của encrypted content để tìm manh mối."""
import base64
import json
from pathlib import Path

# Load multiple encrypted samples
sample_files = list(Path("extract/novels/Chiến Lược Gia Thiên Tài").glob("*.txt"))

print("Analyzing encrypted content structure...")
print("=" * 60)

samples = []
for file in sample_files[:5]:  # Analyze first 5 chapters
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if len(lines) > 2:
            encrypted = lines[2].strip()
            if encrypted.startswith('eyJ'):
                samples.append({
                    'file': file.name,
                    'encrypted': encrypted
                })

print(f"Loaded {len(samples)} encrypted samples")

# Analyze each sample
for i, sample in enumerate(samples, 1):
    print(f"\n{'='*60}")
    print(f"Sample {i}: {sample['file']}")
    print('='*60)
    
    try:
        # Decode base64
        decoded = base64.b64decode(sample['encrypted'])
        data = json.loads(decoded)
        
        print(f"IV: {data['iv'][:50]}...")
        print(f"IV length: {len(data['iv'])}")
        print(f"Value length: {len(data['value'])}")
        print(f"MAC: {data['mac'][:50]}...")
        print(f"MAC length: {len(data['mac'])}")
        
        # Decode IV and value
        iv_bytes = base64.b64decode(data['iv'])
        value_bytes = base64.b64decode(data['value'])
        
        print(f"\nIV bytes length: {len(iv_bytes)}")
        print(f"Value bytes length: {len(value_bytes)}")
        print(f"Value bytes (hex, first 32): {value_bytes[:32].hex()}")
        
        # Check if IV is reused
        if i == 1:
            first_iv = data['iv']
        else:
            if data['iv'] == first_iv:
                print("⚠️  IV is REUSED! (security issue)")
            else:
                print("✅ IV is unique")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Try to find patterns
print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)

print("\n📝 Laravel Encryption Format:")
print("  - Algorithm: AES-256-CBC")
print("  - IV: 16 bytes (random)")
print("  - Key: 32 bytes (APP_KEY)")
print("  - MAC: HMAC-SHA256")

print("\n🔍 To decrypt, we need:")
print("  1. APP_KEY (32 bytes)")
print("  2. IV (provided in encrypted data)")
print("  3. Encrypted value (provided)")

print("\n💡 APP_KEY location possibilities:")
print("  1. Hardcoded in app (not found in strings)")
print("  2. Retrieved from server at runtime")
print("  3. Generated from device/user info")
print("  4. Stored in encrypted SharedPreferences")

print("\n🎯 Next steps:")
print("  1. Use mitmproxy to capture network traffic")
print("  2. Use Frida to hook decrypt function")
print("  3. Extract from app's SharedPreferences")
print("  4. Decompile with reFlutter")
