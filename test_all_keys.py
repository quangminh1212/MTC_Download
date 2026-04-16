#!/usr/bin/env python3
"""Test all found keys to decrypt chapter content."""
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib
from pathlib import Path

def decrypt_laravel(encrypted_b64, key_bytes):
    """Decrypt Laravel encrypted content."""
    try:
        # Parse encrypted JSON
        encrypted_json = json.loads(base64.b64decode(encrypted_b64))

        iv = base64.b64decode(encrypted_json['iv'])
        encrypted_value = base64.b64decode(encrypted_json['value'])

        # Decrypt
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)

        return decrypted.decode('utf-8')
    except Exception as e:
        return None

def main():
    # Read encrypted chapter
    chapter_file = Path('extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt')
    if not chapter_file.exists():
        print("ERROR: Chapter file not found")
        return

    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract encrypted content
    import re
    match = re.search(r'(eyJ[A-Za-z0-9+/=]+)', content)
    if not match:
        print("ERROR: Could not find encrypted content")
        return

    encrypted_b64 = match.group(1)
    print(f"Encrypted content length: {len(encrypted_b64)} bytes")

    # Load all keys
    keys_file = Path('found_keys.txt')
    if not keys_file.exists():
        print("ERROR: found_keys.txt not found")
        return

    with open(keys_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract hex keys
    hex_keys = []
    in_hex_section = False
    for line in lines:
        line = line.strip()
        if line == "=== HEX KEYS ===":
            in_hex_section = True
            continue
        if in_hex_section and line and not line.startswith('==='):
            hex_keys.append(line)

    print(f"\nTesting {len(hex_keys)} hex keys...")
    print("=" * 60)

    for i, hex_key in enumerate(hex_keys, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(hex_keys)}...")

        try:
            # Convert hex to bytes
            key_bytes = bytes.fromhex(hex_key)

            # Only test 32-byte keys (AES-256)
            if len(key_bytes) != 32:
                continue

            result = decrypt_laravel(encrypted_b64, key_bytes)

            if result and len(result) > 100:
                print(f"\n*** SUCCESS! Found working key! ***")
                print(f"Key #{i}: {hex_key}")
                print(f"\nDecrypted content (first 500 chars):")
                print("=" * 60)
                print(result[:500])
                print("=" * 60)

                # Save key
                with open('WORKING_KEY.txt', 'w', encoding='utf-8') as f:
                    f.write(f"Working HEX KEY:\n{hex_key}\n\n")
                    f.write(f"As base64:\nbase64:{base64.b64encode(key_bytes).decode()}\n")

                # Save full decrypted content
                with open('decrypted_chapter1.txt', 'w', encoding='utf-8') as f:
                    f.write(result)

                print(f"\nSaved to WORKING_KEY.txt and decrypted_chapter1.txt")
                return

        except Exception as e:
            continue

    print("\nNo working key found in hex keys.")
    print("Trying to derive keys from hex strings...")

    # Try deriving keys using common methods
    for i, hex_key in enumerate(hex_keys[:50], 1):  # Test first 50
        try:
            # Method 1: SHA256 hash
            key_bytes = hashlib.sha256(hex_key.encode()).digest()
            result = decrypt_laravel(encrypted_b64, key_bytes)
            if result and len(result) > 100:
                print(f"\nSUCCESS with SHA256 hash of key #{i}")
                print(result[:500])
                return

            # Method 2: First 32 bytes of hex
            if len(hex_key) >= 64:
                key_bytes = bytes.fromhex(hex_key[:64])
                result = decrypt_laravel(encrypted_b64, key_bytes)
                if result and len(result) > 100:
                    print(f"\nSUCCESS with first 32 bytes of key #{i}")
                    print(result[:500])
                    return
        except:
            continue

    print("\nNo working key found. Need to continue searching...")

if __name__ == "__main__":
    main()
