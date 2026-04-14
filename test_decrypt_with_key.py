#!/usr/bin/env python3
"""Test giải mã Laravel encryption với APP_KEY."""
import base64
import json
import hashlib
import hmac
from pathlib import Path

def decrypt_laravel(encrypted_content, app_key):
    """
    Giải mã Laravel encryption (AES-256-CBC).
    
    Args:
        encrypted_content: Base64 encoded JSON string
        app_key: Laravel APP_KEY (format: "base64:..." hoặc raw key)
    
    Returns:
        Decrypted string hoặc None nếu thất bại
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
    except ImportError:
        print("❌ Missing pycryptodome. Install with: pip install pycryptodome")
        return None
    
    try:
        # Parse APP_KEY
        if app_key.startswith('base64:'):
            key = base64.b64decode(app_key[7:])
        else:
            key = app_key.encode('utf-8')
        
        # Decode encrypted content
        encrypted_data = json.loads(base64.b64decode(encrypted_content))
        
        # Extract components
        iv = base64.b64decode(encrypted_data['iv'])
        encrypted_value = base64.b64decode(encrypted_data['value'])
        mac = encrypted_data['mac']
        
        # Verify MAC (optional but recommended)
        payload = base64.b64encode(json.dumps({
            'iv': encrypted_data['iv'],
            'value': encrypted_data['value']
        }).encode()).decode()
        
        expected_mac = hmac.new(
            key,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if mac != expected_mac:
            print("⚠️  MAC verification failed (key might be wrong)")
        
        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)
        
        return decrypted.decode('utf-8')
        
    except Exception as e:
        print(f"❌ Decryption failed: {e}")
        return None

def test_with_sample():
    """Test với sample encrypted content."""
    print("Testing Laravel Decryption")
    print("=" * 60)
    
    # Load sample encrypted content
    sample_file = Path("extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt")
    
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        encrypted_content = lines[2].strip() if len(lines) > 2 else ""
    
    if not encrypted_content:
        print("❌ No encrypted content found in sample file")
        return
    
    print(f"Encrypted content length: {len(encrypted_content)}")
    print(f"First 100 chars: {encrypted_content[:100]}...")
    
    # Test with different keys
    test_keys = [
        # Add your keys here
        "base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",  # Example
        # Add more keys from analysis
    ]
    
    print(f"\n{'='*60}")
    print(f"Testing {len(test_keys)} keys...")
    print('='*60)
    
    for i, key in enumerate(test_keys, 1):
        print(f"\nKey {i}: {key[:50]}...")
        result = decrypt_laravel(encrypted_content, key)
        
        if result:
            print(f"✅ SUCCESS!")
            print(f"Decrypted content:")
            print("-" * 60)
            print(result[:500])
            print("-" * 60)
            
            # Save to file
            output_file = Path("decrypted_chapter.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            print(f"\n✅ Full content saved to: {output_file}")
            return True
        else:
            print(f"❌ Failed")
    
    print("\n" + "=" * 60)
    print("❌ All keys failed")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Add more keys to test_keys list")
    print("  2. Use mitmproxy to capture the correct key")
    print("  3. Use Frida to hook decrypt function")
    
    return False

def test_with_custom_key():
    """Test với custom key từ user."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_decrypt_with_key.py <APP_KEY>")
        print("\nExample:")
        print("  python test_decrypt_with_key.py 'base64:abcd1234...'")
        return
    
    app_key = sys.argv[1]
    
    print("Testing with custom key")
    print("=" * 60)
    print(f"Key: {app_key[:50]}...")
    
    # Load sample
    sample_file = Path("extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt")
    
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        encrypted_content = lines[2].strip() if len(lines) > 2 else ""
    
    result = decrypt_laravel(encrypted_content, app_key)
    
    if result:
        print(f"\n✅ SUCCESS!")
        print(f"Decrypted content:")
        print("-" * 60)
        print(result)
        print("-" * 60)
        
        # Save to file
        output_file = Path("decrypted_chapter.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"\n✅ Full content saved to: {output_file}")
    else:
        print(f"\n❌ Decryption failed with this key")

def main():
    import sys
    
    if len(sys.argv) > 1:
        # Test with custom key
        test_with_custom_key()
    else:
        # Test with predefined keys
        test_with_sample()

if __name__ == "__main__":
    main()
