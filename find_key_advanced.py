#!/usr/bin/env python3
"""Advanced key finder - extract all potential keys from libapp.so"""
import re
from pathlib import Path

def extract_base64_keys(file_path):
    """Extract all base64-like strings that could be keys."""
    with open(file_path, 'rb') as f:
        data = f.read()

    # Find all base64: patterns
    pattern = rb'base64:([A-Za-z0-9+/=]{32,})'
    matches = re.findall(pattern, data)

    keys = []
    for match in matches:
        try:
            key = match.decode('utf-8')
            if len(key) >= 32:  # AES-256 needs 32+ chars
                keys.append(f"base64:{key}")
        except:
            pass

    return keys

def extract_hex_keys(file_path):
    """Extract potential hex keys."""
    with open(file_path, 'rb') as f:
        data = f.read()

    # Find 32-byte hex strings (AES-256)
    pattern = rb'([0-9a-fA-F]{64})'
    matches = re.findall(pattern, data)

    keys = []
    for match in matches:
        try:
            key = match.decode('utf-8')
            keys.append(key)
        except:
            pass

    return keys

def main():
    libapp = Path('extract/lib/arm64-v8a/libapp.so')

    if not libapp.exists():
        print("ERROR: libapp.so not found")
        return

    print("Searching for encryption keys in libapp.so...")
    print("=" * 60)

    # Extract base64 keys
    base64_keys = extract_base64_keys(libapp)
    print(f"\nFound {len(base64_keys)} base64 keys:")
    for i, key in enumerate(base64_keys[:20], 1):  # Show first 20
        print(f"  [{i}] {key[:60]}...")

    # Extract hex keys
    hex_keys = extract_hex_keys(libapp)
    print(f"\nFound {len(hex_keys)} hex keys:")
    for i, key in enumerate(hex_keys[:20], 1):  # Show first 20
        print(f"  [{i}] {key}")

    # Save all keys
    output = Path('found_keys.txt')
    with open(output, 'w', encoding='utf-8') as f:
        f.write("=== BASE64 KEYS ===\n")
        for key in base64_keys:
            f.write(f"{key}\n")

        f.write("\n=== HEX KEYS ===\n")
        for key in hex_keys:
            f.write(f"{key}\n")

    print(f"\nSaved all keys to {output}")
    print(f"   Total: {len(base64_keys)} base64 + {len(hex_keys)} hex keys")

if __name__ == "__main__":
    main()
