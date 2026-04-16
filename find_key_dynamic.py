#!/usr/bin/env python3
"""
Dynamic key finding - simulate app behavior to find key.
"""
import json
import base64
import re
import hashlib
from pathlib import Path

def simulate_key_generation():
    """Simulate possible key generation methods."""
    print("Simulating key generation methods...")
    print("=" * 60)

    # Common device IDs and user tokens
    device_ids = [
        "android_id_1234567890",
        "device_abcdef123456",
        "imei_123456789012345",
        "serial_xyz123456",
    ]

    user_tokens = [
        "user_token_abc123",
        "auth_token_xyz789",
        "session_token_123abc",
        "bearer_token_456def",
    ]

    # App-specific strings
    app_strings = [
        "mtruyen", "MTC", "novelfever", "lonoapp",
        "com.lonoapp.mtc", "mtruyen.com",
    ]

    generated_keys = []

    # Method 1: SHA256 of combinations
    for device_id in device_ids:
        for app_str in app_strings:
            key = hashlib.sha256(f"{device_id}:{app_str}".encode()).digest()
            generated_keys.append(("SHA256(device+app)", key))

    # Method 2: SHA256 of user token + device
    for token in user_tokens:
        for device_id in device_ids:
            key = hashlib.sha256(f"{token}:{device_id}".encode()).digest()
            generated_keys.append(("SHA256(token+device)", key))

    # Method 3: Simple concatenation (32 bytes)
    for base in app_strings:
        if len(base) < 32:
            padded = base.ljust(32, '0')[:32]
            key = padded.encode()
            generated_keys.append(("Padded app name", key))

    print(f"Generated {len(generated_keys)} potential keys")
    return generated_keys

def test_keys(generated_keys):
    """Test generated keys against encrypted content."""
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

    print(f"\nTesting {len(generated_keys)} generated keys...")
    print("=" * 60)

    for i, (desc, key_bytes) in enumerate(generated_keys, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(generated_keys)}...")

        try:
            # Try to decrypt
            encrypted_json = json.loads(base64.b64decode(encrypted_b64))
            iv = base64.b64decode(encrypted_json['iv'])
            encrypted_value = base64.b64decode(encrypted_json['value'])

            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad

            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)

            # Check if result looks like text
            result = decrypted.decode('utf-8', errors='ignore')
            if len(result) > 100 and all(ord(c) < 128 for c in result[:100]):
                print(f"\n*** SUCCESS! ***")
                print(f"Method: {desc}")
                print(f"Key (hex): {key_bytes.hex()}")
                print(f"Key (base64): base64:{base64.b64encode(key_bytes).decode()}")
                print(f"\nDecrypted preview:")
                print(result[:200])

                # Save key
                with open('DYNAMIC_KEY.txt', 'w', encoding='utf-8') as f:
                    f.write(f"Dynamic key found!\n\n")
                    f.write(f"Method: {desc}\n")
                    f.write(f"Hex: {key_bytes.hex()}\n")
                    f.write(f"Base64: base64:{base64.b64encode(key_bytes).decode()}\n")

                return True
        except:
            continue

    print("\nNo working key found with dynamic generation.")
    return False

def main():
    print("Dynamic Key Finder for MTC App")
    print("=" * 60)

    # Step 1: Simulate key generation
    generated_keys = simulate_key_generation()

    # Step 2: Test keys
    success = test_keys(generated_keys)

    if not success:
        print("\n" + "=" * 60)
        print("CONCLUSION:")
        print("Key is likely:")
        print("  1. Retrieved from server at runtime")
        print("  2. Stored in Android KeyStore")
        print("  3. Generated from server-side secret + client info")
        print("\nNEXT STEPS:")
        print("  1. Run app with mitmproxy to capture key exchange")
        print("  2. Use Frida to hook key retrieval functions")
        print("  3. Check server response for 'X-Encryption-Key' header")

if __name__ == "__main__":
    main()
