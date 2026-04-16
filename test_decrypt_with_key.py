#!/usr/bin/env python3
"""
Quick script to test a key against encrypted content.
Usage: python test_decrypt_with_key.py "base64:YOUR_KEY_HERE"
"""
import sys
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pathlib import Path
import re

def decrypt_laravel(encrypted_b64, app_key):
    """Decrypt Laravel encrypted content."""
    try:
        # Parse encrypted JSON
        encrypted_json = json.loads(base64.b64decode(encrypted_b64))

        iv = base64.b64decode(encrypted_json['iv'])
        encrypted_value = base64.b64decode(encrypted_json['value'])

        # Extract key
        if app_key.startswith('base64:'):
            key = base64.b64decode(app_key[7:])
        else:
            key = app_key.encode()

        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)

        return decrypted.decode('utf-8')

    except Exception as e:
        print(f"Decryption failed: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_decrypt_with_key.py <APP_KEY>")
        print("Example: python test_decrypt_with_key.py 'base64:YOUR_KEY_HERE'")
        return

    app_key = sys.argv[1]

    # Read encrypted chapter
    chapter_file = Path('extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt')
    if not chapter_file.exists():
        print(f"ERROR: {chapter_file} not found")
        return

    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract encrypted content
    match = re.search(r'(eyJ[A-Za-z0-9+/=]+)', content)
    if not match:
        print("ERROR: Could not find encrypted content")
        return

    encrypted_b64 = match.group(1)

    print(f"Testing key: {app_key[:50]}...")
    print("=" * 60)

    result = decrypt_laravel(encrypted_b64, app_key)

    if result:
        print("\n*** SUCCESS! Key works! ***\n")
        print("Decrypted content (first 1000 chars):")
        print("=" * 60)
        print(result[:1000])
        print("=" * 60)

        # Save
        with open('WORKING_KEY.txt', 'w', encoding='utf-8') as f:
            f.write(f"Working APP_KEY:\n{app_key}\n")

        with open('decrypted_chapter1.txt', 'w', encoding='utf-8') as f:
            f.write(result)

        print(f"\nSaved to WORKING_KEY.txt and decrypted_chapter1.txt")
    else:
        print("\n*** FAILED! Key does not work. ***")

if __name__ == "__main__":
    main()
