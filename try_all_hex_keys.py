#!/usr/bin/env python3
"""Thử tất cả các hex keys tìm được với nhiều phương pháp giải mã."""
import base64
import json
import re
from pathlib import Path

def decrypt_laravel_cbc(encrypted_content, key_bytes):
    """Giải mã Laravel encryption (AES-256-CBC)."""
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
        if len(key_bytes) != 32:
            return None
        
        # Decode encrypted content
        encrypted_data = json.loads(base64.b64decode(encrypted_content))
        
        # Extract components
        iv = base64.b64decode(encrypted_data['iv'])
        encrypted_value = base64.b64decode(encrypted_data['value'])
        
        # Decrypt
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)
        
        return decrypted.decode('utf-8')
        
    except Exception as e:
        return None

def decrypt_aes_ecb(encrypted_content, key_bytes):
    """Giải mã AES-256-ECB (thử với IV = 0)."""
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
    except ImportError:
        return None
    
    try:
        if len(key_bytes) != 32:
            return None
        
        # Decode encrypted content
        encrypted_data = json.loads(base64.b64decode(encrypted_content))
        
        # Extract components
        iv = base64.b64decode(encrypted_data['iv'])
        encrypted_value = base64.b64decode(encrypted_data['value'])
        
        # Try ECB mode (ignore IV)
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)
        
        return decrypted.decode('utf-8')
        
    except Exception as e:
        return None

def try_key_variations(key_hex):
    """Thử các biến thể của key."""
    variations = []
    
    # Original hex
    try:
        key_bytes = bytes.fromhex(key_hex)
        if len(key_bytes) == 32:
            variations.append(('original', key_bytes))
    except:
        pass
    
    # First 32 bytes
    try:
        if len(key_hex) >= 64:
            key_bytes = bytes.fromhex(key_hex[:64])
            if len(key_bytes) == 32:
                variations.append(('first32', key_bytes))
    except:
        pass
    
    # Last 32 bytes
    try:
        if len(key_hex) >= 64:
            key_bytes = bytes.fromhex(key_hex[-64:])
            if len(key_bytes) == 32:
                variations.append(('last32', key_bytes))
    except:
        pass
    
    # Reversed
    try:
        key_bytes = bytes.fromhex(key_hex[::-1])
        if len(key_bytes) == 32:
            variations.append(('reversed', key_bytes))
    except:
        pass
    
    return variations

def main():
    print("=" * 60)
    print("THỬ TẤT CẢ HEX KEYS VỚI NHIỀU PHƯƠNG PHÁP")
    print("=" * 60)
    
    # Load sample encrypted content
    sample_file = Path("extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt")
    
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        encrypted_content = lines[2].strip() if len(lines) > 2 else ""
    
    print(f"Encrypted content length: {len(encrypted_content)}")
    
    # Read all hex keys from dart_snapshot_strings.txt
    strings_file = Path("dart_snapshot_strings.txt")
    if not strings_file.exists():
        print("❌ dart_snapshot_strings.txt not found")
        return
    
    with open(strings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all hex strings (32+ chars)
    hex_pattern = re.compile(r'^[0-9a-fA-F]{32,}$', re.MULTILINE)
    hex_keys = hex_pattern.findall(content)
    
    print(f"Found {len(hex_keys)} hex keys")
    
    # Also add keys from libapp_strings.txt
    libapp_strings = Path("libapp_strings.txt")
    if libapp_strings.exists():
        with open(libapp_strings, 'r', encoding='utf-8') as f:
            libapp_content = f.read()
        hex_keys.extend(hex_pattern.findall(libapp_content))
    
    # Remove duplicates
    hex_keys = list(set(hex_keys))
    print(f"Total unique hex keys: {len(hex_keys)}")
    
    # Test each key
    print("\n" + "=" * 60)
    print("TESTING KEYS...")
    print("=" * 60)
    
    tested = 0
    for key_hex in hex_keys:
        variations = try_key_variations(key_hex)
        
        for var_name, key_bytes in variations:
            tested += 1
            if tested % 100 == 0:
                print(f"Progress: {tested}...")
            
            # Try CBC
            result = decrypt_laravel_cbc(encrypted_content, key_bytes)
            if result and len(result) > 100:
                print(f"\n{'='*60}")
                print(f"✅ SUCCESS with CBC!")
                print(f"{'='*60}")
                print(f"Key hex: {key_hex}")
                print(f"Variation: {var_name}")
                print(f"Key bytes: {key_bytes.hex()}")
                print(f"\nDecrypted content (first 500 chars):")
                print("-" * 60)
                print(result[:500])
                print("-" * 60)
                
                # Save result
                output_file = Path("decrypted_chapter.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                print(f"\n✅ Full content saved to: {output_file}")
                
                # Save key
                key_file = Path("APP_KEY.txt")
                with open(key_file, 'w') as f:
                    f.write(f"base64:{base64.b64encode(key_bytes).decode()}")
                
                print(f"✅ Key saved to: {key_file}")
                return
            
            # Try ECB
            result = decrypt_aes_ecb(encrypted_content, key_bytes)
            if result and len(result) > 100:
                print(f"\n{'='*60}")
                print(f"✅ SUCCESS with ECB!")
                print(f"{'='*60}")
                print(f"Key hex: {key_hex}")
                print(f"Variation: {var_name}")
                print(f"Key bytes: {key_bytes.hex()}")
                print(f"\nDecrypted content (first 500 chars):")
                print("-" * 60)
                print(result[:500])
                print("-" * 60)
                
                # Save result
                output_file = Path("decrypted_chapter.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                print(f"\n✅ Full content saved to: {output_file}")
                
                # Save key
                key_file = Path("APP_KEY.txt")
                with open(key_file, 'w') as f:
                    f.write(f"base64:{base64.b64encode(key_bytes).decode()}")
                
                print(f"✅ Key saved to: {key_file}")
                return
    
    print(f"\n{'='*60}")
    print(f"❌ Tested {tested} key variations, none worked")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("1. Use mitmproxy to capture traffic")
    print("2. Use Frida to hook decrypt function")
    print("3. Decompile Dart code with reFlutter")

if __name__ == "__main__":
    main()
