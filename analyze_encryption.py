#!/usr/bin/env python3
"""
Analyze encryption format and try to find key through analysis.
"""
import json
import base64
import re
from pathlib import Path

def analyze_encryption():
    """Analyze the encryption format."""
    # Read encrypted chapter
    chapter_file = Path('extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt')
    if not chapter_file.exists():
        print("ERROR: Chapter file not found")
        return

    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract encrypted content
    match = re.search(r'(eyJ[A-Za-z0-9+/=]+)', content)
    if not match:
        print("ERROR: Could not find encrypted content")
        return

    encrypted_b64 = match.group(1)

    print("Analyzing encryption format...")
    print("=" * 60)

    try:
        # Decode the encrypted JSON
        encrypted_json = json.loads(base64.b64decode(encrypted_b64))

        print("Encryption structure:")
        print(f"  IV length: {len(encrypted_json['iv'])} chars")
        print(f"  Value length: {len(encrypted_json['value'])} chars")
        print(f"  MAC length: {len(encrypted_json['mac'])} chars")

        # Decode IV and value
        iv = base64.b64decode(encrypted_json['iv'])
        encrypted_value = base64.b64decode(encrypted_json['value'])

        print(f"\nBinary analysis:")
        print(f"  IV bytes: {len(iv)} bytes")
        print(f"  Value bytes: {len(encrypted_value)} bytes")
        print(f"  IV (hex): {iv.hex()[:50]}...")
        print(f"  Value (hex first 50): {encrypted_value.hex()[:50]}...")

        # Check if it's Laravel format
        print(f"\nLaravel format check:")
        print(f"  Has 'iv', 'value', 'mac': {'iv' in encrypted_json and 'value' in encrypted_json and 'mac' in encrypted_json}")
        print(f"  IV is 16 bytes (AES block size): {len(iv) == 16}")
        print(f"  Value length multiple of 16: {len(encrypted_value) % 16 == 0}")

        # Try to guess key length
        print(f"\nKey analysis:")
        print("  Laravel uses 32-byte keys (AES-256)")
        print("  Key is base64 encoded in .env file as APP_KEY=base64:...")

        # Look for patterns in the encrypted data
        print(f"\nPattern analysis:")
        # Check if there's any readable text in the encrypted data
        try:
            # Try to decode as UTF-8
            decoded = encrypted_value[:100].decode('utf-8', errors='ignore')
            if any(c.isprintable() for c in decoded):
                print(f"  Possible plaintext in encrypted data: {decoded[:50]}")
        except:
            pass

        # Check for common Laravel patterns
        print(f"\nLaravel-specific patterns:")
        print("  Laravel uses CBC mode with PKCS7 padding")
        print("  MAC is SHA256 of iv+value+key")

        return encrypted_json

    except Exception as e:
        print(f"Analysis error: {e}")
        return None

def try_key_derivation(encrypted_json):
    """Try to derive key from known patterns."""
    print("\n" + "=" * 60)
    print("Trying key derivation methods...")

    iv = base64.b64decode(encrypted_json['iv'])
    encrypted_value = base64.b64decode(encrypted_json['value'])

    # Common Laravel key patterns
    common_bases = [
        'mtruyen', 'MTC', 'novelfever', 'lonoapp',
        'mtruyen.com', 'api.mtruyen.com',
        '12345678901234567890123456789012',
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    ]

    import hashlib

    for base in common_bases:
        # SHA256 hash
        key = hashlib.sha256(base.encode()).digest()
        print(f"  SHA256('{base[:20]}...'): {key.hex()[:20]}...")

        # Try decrypting
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad

            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)

            # Check if result looks like text
            result = decrypted.decode('utf-8', errors='ignore')
            if len(result) > 100 and all(ord(c) < 128 for c in result[:100]):
                print(f"    SUCCESS! Key works!")
                print(f"    Decrypted: {result[:100]}")
                return key
        except:
            continue

    print("No key found through derivation.")
    return None

def main():
    encrypted_json = analyze_encryption()
    if encrypted_json:
        try_key_derivation(encrypted_json)

    print("\n" + "=" * 60)
    print("RECOMMENDATION:")
    print("The key is likely dynamically generated or stored in:")
    print("  1. SharedPreferences (Android)")
    print("  2. KeyStore (Android)")
    print("  3. Server response headers")
    print("  4. Generated from device ID + user token")
    print("\nUse mitmproxy or Frida to capture the key at runtime.")

if __name__ == "__main__":
    main()
