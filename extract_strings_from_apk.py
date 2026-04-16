#!/usr/bin/env python3
"""Extract all strings from APK that could be encryption keys."""
import re
from pathlib import Path
import zipfile

def extract_strings_from_dex(dex_file):
    """Extract strings from DEX file."""
    strings = []
    with open(dex_file, 'rb') as f:
        data = f.read()

    # Find printable ASCII strings (min 20 chars)
    pattern = rb'[ -~]{20,}'
    matches = re.findall(pattern, data)

    for match in matches:
        try:
            s = match.decode('utf-8')
            # Look for base64 or key-like patterns
            if any(keyword in s.lower() for keyword in ['key', 'secret', 'encrypt', 'base64:', 'app_key']):
                strings.append(s)
        except:
            pass

    return strings

def main():
    print("Extracting strings from APK...")
    print("=" * 60)

    # Check DEX files
    dex_files = [
        'extract/classes.dex',
        'extract/classes2.dex',
        'extract/classes3.dex',
    ]

    all_strings = []

    for dex_file in dex_files:
        dex_path = Path(dex_file)
        if not dex_path.exists():
            continue

        print(f"\nProcessing {dex_file}...")
        strings = extract_strings_from_dex(dex_path)
        all_strings.extend(strings)
        print(f"  Found {len(strings)} potential key strings")

    # Remove duplicates
    all_strings = list(set(all_strings))

    print(f"\nTotal unique strings: {len(all_strings)}")

    # Filter for likely keys
    likely_keys = []
    for s in all_strings:
        # Base64 format keys
        if s.startswith('base64:') and len(s) > 40:
            likely_keys.append(s)
        # Long alphanumeric strings
        elif re.match(r'^[A-Za-z0-9+/=]{32,}$', s):
            likely_keys.append(f"base64:{s}")

    print(f"\nLikely encryption keys: {len(likely_keys)}")
    for i, key in enumerate(likely_keys[:20], 1):
        print(f"  [{i}] {key[:70]}...")

    # Save all
    output = Path('extracted_strings.txt')
    with open(output, 'w', encoding='utf-8') as f:
        f.write("=== ALL STRINGS ===\n")
        for s in sorted(all_strings):
            f.write(f"{s}\n")

        f.write("\n=== LIKELY KEYS ===\n")
        for key in likely_keys:
            f.write(f"{key}\n")

    print(f"\nSaved to {output}")

    # Test these keys
    if likely_keys:
        print("\nTesting likely keys...")
        test_keys(likely_keys)

def test_keys(keys):
    """Test keys against encrypted content."""
    import json
    import base64
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad

    # Read encrypted chapter
    chapter_file = Path('extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt')
    if not chapter_file.exists():
        return

    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'(eyJ[A-Za-z0-9+/=]+)', content)
    if not match:
        return

    encrypted_b64 = match.group(1)

    for i, key_str in enumerate(keys, 1):
        try:
            # Extract key
            if key_str.startswith('base64:'):
                key = base64.b64decode(key_str[7:])
            else:
                key = key_str.encode()

            if len(key) != 32:
                continue

            # Try decrypt
            encrypted_json = json.loads(base64.b64decode(encrypted_b64))
            iv = base64.b64decode(encrypted_json['iv'])
            encrypted_value = base64.b64decode(encrypted_json['value'])

            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)
            result = decrypted.decode('utf-8')

            if len(result) > 100:
                print(f"\n*** SUCCESS! Key #{i} works! ***")
                print(f"Key: {key_str}")
                print(f"\nContent preview:")
                print(result[:500])

                with open('WORKING_KEY.txt', 'w', encoding='utf-8') as f:
                    f.write(f"Working key:\n{key_str}\n")

                return
        except:
            pass

    print("No working key found in extracted strings.")

if __name__ == "__main__":
    main()
