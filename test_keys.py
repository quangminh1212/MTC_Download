#!/usr/bin/env python3
"""Test potential APP_KEYs found in APK."""
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib

# Potential keys found in libapp.so (converted to base64 format)
POTENTIAL_KEYS = [
    "base64:ZixhxDDYTqT+ZqdzPQt2t7+T68SvL0klauWBAf7pKwQ=",
    "base64:BNtP8Q7AV+muJrB9AoC39DQdpdGx6uBsfZsvL22cVig=",
    "base64:fU2bAJvGaEKuzaEq5qOA5iiB/y8tgsaFKKpgVlg6SPM=",
    "base64:BIvSrrnLflfLLEtIL/yBt6+53ifh470jwjpEU72azjI=",
    "base64:BEO9fpr7U9i4Uom8xI7lv+byATfRCgh+tueHHioQpZk=",
]

def decrypt_laravel(encrypted_b64, app_key):
    """Decrypt Laravel encrypted content."""
    try:
        # Parse encrypted JSON
        encrypted_json = json.loads(base64.b64decode(encrypted_b64))

        iv = base64.b64decode(encrypted_json['iv'])
        encrypted_value = base64.b64decode(encrypted_json['value'])
        mac = encrypted_json['mac']

        # Extract key from base64: format
        if app_key.startswith('base64:'):
            key = base64.b64decode(app_key[7:])
        else:
            key = app_key.encode()

        # Verify MAC
        payload = base64.b64encode(encrypted_json['iv'].encode() + encrypted_value).decode()
        expected_mac = hashlib.sha256(f"{payload}{key.hex()}".encode()).hexdigest()

        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)

        return decrypted.decode('utf-8')

    except Exception as e:
        return None

def main():
    # Read encrypted chapter
    with open('extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract encrypted JSON
    import re
    match = re.search(r'(eyJ[A-Za-z0-9+/=]+)', content)
    if not match:
        print("Could not find encrypted content")
        return

    encrypted_b64 = match.group(1)
    print(f"Testing {len(POTENTIAL_KEYS)} potential keys...\n")

    for i, key in enumerate(POTENTIAL_KEYS):
        print(f"[{i+1}/{len(POTENTIAL_KEYS)}] Testing: {key[:30]}...")

        result = decrypt_laravel(encrypted_b64, key)

        if result:
            print(f"\nSUCCESS! Found working key!")
            print(f"Key: {key}")
            print(f"\nDecrypted content (first 500 chars):")
            print("="*60)
            print(result[:500])
            print("="*60)

            # Save key
            with open('APP_KEY.txt', 'w', encoding='utf-8') as f:
                f.write(f"Working APP_KEY:\n{key}\n")

            # Save decrypted sample
            with open('decrypted_sample.txt', 'w', encoding='utf-8') as f:
                f.write(result)

            print(f"\n✓ Saved to APP_KEY.txt and decrypted_sample.txt")
            return
        else:
            print("   Failed")

    print("\nNone of the keys worked. Need to continue searching...")

if __name__ == "__main__":
    main()
