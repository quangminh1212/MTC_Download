#!/usr/bin/env python3
"""Thử các common Laravel APP_KEYs và patterns."""
import base64
import json
import hashlib
import hmac
from pathlib import Path

def decrypt_laravel(encrypted_content, app_key):
    """Giải mã Laravel encryption."""
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
    except ImportError:
        print("Installing pycryptodome...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pycryptodome'])
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
    
    try:
        # Parse APP_KEY
        if isinstance(app_key, str):
            if app_key.startswith('base64:'):
                key = base64.b64decode(app_key[7:])
            else:
                key = app_key.encode('utf-8')
        else:
            key = app_key
        
        # Ensure key is 32 bytes
        if len(key) != 32:
            return None
        
        # Decode encrypted content
        encrypted_data = json.loads(base64.b64decode(encrypted_content))
        
        # Extract components
        iv = base64.b64decode(encrypted_data['iv'])
        encrypted_value = base64.b64decode(encrypted_data['value'])
        
        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)
        
        return decrypted.decode('utf-8')
        
    except Exception as e:
        return None

# Load sample encrypted content
sample_file = Path("extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt")

if not sample_file.exists():
    print(f"❌ Sample file not found: {sample_file}")
    exit(1)

with open(sample_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    encrypted_content = lines[2].strip() if len(lines) > 2 else ""

print("Trying common Laravel APP_KEYs...")
print("=" * 60)

# Generate common keys to try
test_keys = []

# 1. Common patterns
common_patterns = [
    b'0' * 32,  # All zeros
    b'1' * 32,  # All ones
    b'a' * 32,  # All 'a'
    b'novelfever' + b'0' * 21,  # App name padded
    b'lonoapp' + b'0' * 24,  # Company name padded
    b'truyen.onl' + b'0' * 21,  # Domain padded
]

for pattern in common_patterns:
    test_keys.append(('base64:' + base64.b64encode(pattern).decode(), f"Pattern: {pattern[:10]}..."))

# 2. Try MD5/SHA256 of common strings
common_strings = [
    'novelfever',
    'lonoapp',
    'truyen.onl',
    'NovelFever',
    'LonoApp',
    'Truyen.onl',
    'NOVELFEVER',
    'LONOAPP',
    'TRUYEN.ONL',
    'com.lonoapp.novelfever',
    'secret',
    'password',
    '12345678',
    'admin',
]

for s in common_strings:
    # MD5 (16 bytes) + MD5 again = 32 bytes
    md5_key = hashlib.md5(s.encode()).digest() + hashlib.md5((s + s).encode()).digest()
    test_keys.append(('base64:' + base64.b64encode(md5_key).decode(), f"MD5: {s}"))
    
    # SHA256 (32 bytes)
    sha256_key = hashlib.sha256(s.encode()).digest()
    test_keys.append(('base64:' + base64.b64encode(sha256_key).decode(), f"SHA256: {s}"))

# 3. Try keys from strings (hex keys found earlier)
hex_keys_from_strings = [
    "ffffffffffffffffffffffffffffffff6c611070995ad10045841b09b761b893",
    "9b9f605f5a858107ab1ec85e6b41c8aacf846e86789051d37998f7b9022d7598",
]

for hex_key in hex_keys_from_strings:
    try:
        key_bytes = bytes.fromhex(hex_key)
        if len(key_bytes) == 32:
            test_keys.append(('base64:' + base64.b64encode(key_bytes).decode(), f"Hex from strings: {hex_key[:20]}..."))
    except:
        pass

print(f"Testing {len(test_keys)} keys...")
print("=" * 60)

for i, (key, desc) in enumerate(test_keys, 1):
    if i % 10 == 0:
        print(f"Progress: {i}/{len(test_keys)}...")
    
    result = decrypt_laravel(encrypted_content, key)
    
    if result and len(result) > 100:  # Successful decryption should be long
        print(f"\n✅ SUCCESS with key #{i}!")
        print(f"Description: {desc}")
        print(f"Key: {key[:60]}...")
        print("\nDecrypted content:")
        print("=" * 60)
        print(result[:500])
        print("=" * 60)
        
        # Save result
        output_file = Path("decrypted_chapter.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"\n✅ Full content saved to: {output_file}")
        
        # Save key
        key_file = Path("APP_KEY.txt")
        with open(key_file, 'w') as f:
            f.write(key)
        
        print(f"✅ Key saved to: {key_file}")
        exit(0)

print("\n" + "=" * 60)
print("❌ All keys failed")
print("=" * 60)
print("\nThe APP_KEY is not a common pattern.")
print("Need to use mitmproxy or Frida to capture it from the app.")
