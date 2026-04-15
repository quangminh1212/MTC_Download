#!/usr/bin/env python3
"""Phân tích flow mã hóa của app để tìm key."""
import base64
import json
import hashlib
from pathlib import Path

def analyze_encrypted_content():
    """Phân tích nội dung đã mã hóa."""
    sample_file = Path("extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt")
    
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        encrypted_content = lines[2].strip() if len(lines) > 2 else ""
    
    print("Phân tích nội dung đã mã hóa:")
    print("=" * 60)
    
    # Decode base64
    try:
        # The content is base64 encoded JSON
        # Remove any whitespace and newlines
        encrypted_content = encrypted_content.replace('\n', '').replace('\r', '').replace(' ', '')
        
        # Add padding if needed
        missing_padding = len(encrypted_content) % 4
        if missing_padding:
            encrypted_content += '=' * (4 - missing_padding)
        
        # First base64 decode
        decoded = base64.b64decode(encrypted_content)
        print(f"✅ Base64 decoded: {len(decoded)} bytes")
        
        # The decoded content should be a JSON string
        # Try to decode as UTF-8 with error handling
        try:
            json_str = decoded.decode('utf-8', errors='replace')
            print(f"✅ Decoded as UTF-8 string (with replacements)")
            print(f"   First 100 chars: {json_str[:100]}")
            
            # Parse JSON
            data = json.loads(json_str)
            print(f"✅ JSON parsed")
            print(f"   Keys: {list(data.keys())}")
        except Exception as e:
            print(f"❌ Error parsing JSON: {e}")
            print(f"   Decoded bytes (first 50): {decoded[:50]}")
            return None
        
        # Extract components
        iv = base64.b64decode(data['iv'])
        value = base64.b64decode(data['value'])
        mac = data.get('mac', '')
        
        print(f"\n📊 Components:")
        print(f"   IV: {len(iv)} bytes = {data['iv']}")
        print(f"   Value: {len(value)} bytes")
        print(f"   MAC: {mac[:50]}..." if mac else "   MAC: None")
        
        # Analyze IV
        print(f"\n🔍 IV Analysis:")
        print(f"   IV hex: {iv.hex()}")
        print(f"   IV is zeros: {iv == b'\\x00' * 16}")
        print(f"   IV is sequential: {iv == bytes(range(16))}")
        
        # Analyze value
        print(f"\n🔍 Value Analysis:")
        print(f"   First 32 bytes: {value[:32].hex()}")
        print(f"   Last 32 bytes: {value[-32:].hex()}")
        
        # Check if value is multiple of 16 (AES block size)
        print(f"   Value length % 16: {len(value) % 16}")
        
        # Try to find patterns
        print(f"\n🔍 Pattern Analysis:")
        
        # Check if encrypted content has patterns
        if len(value) >= 32:
            first_block = value[:16]
            second_block = value[16:32]
            print(f"   First block: {first_block.hex()}")
            print(f"   Second block: {second_block.hex()}")
            print(f"   Blocks are same: {first_block == second_block}")
        
        # MAC analysis
        if mac:
            print(f"\n🔍 MAC Analysis:")
            print(f"   MAC length: {len(mac)}")
            print(f"   MAC is hex: {all(c in '0123456789abcdef' for c in mac.lower())}")
            
            # MAC is likely HMAC-SHA256 (64 hex chars)
            if len(mac) == 64:
                print(f"   MAC is HMAC-SHA256")
        
        # Try to guess key derivation
        print(f"\n🔍 Key Derivation Guesses:")
        
        # Common key derivation methods
        # 1. Key from IV
        # 2. Key from MAC
        # 3. Key from device ID
        # 4. Key from user ID
        # 5. Key from book ID + chapter ID
        
        # Get book and chapter info from file
        book_id = 153347  # Chiến Lược Gia Thiên Tài
        chapter_id = 123456  # Placeholder
        
        # Try key from IV
        print(f"\n   Trying key from IV...")
        key_from_iv = iv * 2  # 16 bytes -> 32 bytes
        print(f"   Key from IV (doubled): {key_from_iv.hex()}")
        
        # Try key from MAC
        if mac:
            print(f"\n   Trying key from MAC...")
            key_from_mac = bytes.fromhex(mac[:64])  # First 32 bytes of MAC
            print(f"   Key from MAC: {key_from_mac.hex()}")
        
        # Try key from book_id + chapter_id
        print(f"\n   Trying key from IDs...")
        key_from_ids = hashlib.sha256(f"{book_id}_{chapter_id}".encode()).digest()
        print(f"   Key from SHA256(book_chapter): {key_from_ids.hex()}")
        
        # Try key from IV + MAC
        if mac:
            print(f"\n   Trying key from IV + MAC...")
            combined = iv + bytes.fromhex(mac[:32])
            key_from_combined = hashlib.sha256(combined).digest()
            print(f"   Key from SHA256(IV + MAC): {key_from_combined.hex()}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def try_derived_keys():
    """Thử các key được derive từ các thông tin có sẵn."""
    print("\n" + "=" * 60)
    print("THỬ CÁC KEY ĐƯỢC DERIVE")
    print("=" * 60)
    
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    
    # Load encrypted content
    sample_file = Path("extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt")
    with open(sample_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        encrypted_content = lines[2].strip() if len(lines) > 2 else ""
    
    # Add padding if needed
    missing_padding = len(encrypted_content) % 4
    if missing_padding:
        encrypted_content += '=' * (4 - missing_padding)
    
    data = json.loads(base64.b64decode(encrypted_content))
    iv = base64.b64decode(data['iv'])
    value = base64.b64decode(data['value'])
    mac = data.get('mac', '')
    
    # Keys to try
    keys_to_try = []
    
    # 1. Key from IV (doubled)
    keys_to_try.append(("IV doubled", iv * 2))
    
    # 2. Key from MAC
    if mac and len(mac) >= 64:
        keys_to_try.append(("MAC", bytes.fromhex(mac[:64])))
    
    # 3. Key from SHA256(IV)
    keys_to_try.append(("SHA256(IV)", hashlib.sha256(iv).digest()))
    
    # 4. Key from SHA256(IV + MAC)
    if mac:
        combined = iv + bytes.fromhex(mac[:32])
        keys_to_try.append(("SHA256(IV+MAC)", hashlib.sha256(combined).digest()))
    
    # 5. Key from book_id
    book_id = 153347
    keys_to_try.append(("SHA256(book_id)", hashlib.sha256(str(book_id).encode()).digest()))
    
    # 6. Key from common patterns
    keys_to_try.append(("zeros", b'\x00' * 32))
    keys_to_try.append(("ones", b'\xff' * 32))
    
    # Try each key
    for name, key in keys_to_try:
        if len(key) != 32:
            continue
        
        try:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(value), AES.block_size)
            
            # Check if decrypted content is valid UTF-8
            text = decrypted.decode('utf-8')
            
            print(f"\n✅ SUCCESS with key: {name}")
            print(f"   Key: {key.hex()}")
            print(f"   Decrypted (first 200 chars): {text[:200]}")
            
            # Save result
            with open("decrypted_chapter.txt", 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"   ✅ Saved to decrypted_chapter.txt")
            
            # Save key
            with open("APP_KEY.txt", 'w') as f:
                f.write(f"base64:{base64.b64encode(key).decode()}")
            print(f"   ✅ Key saved to APP_KEY.txt")
            
            return True
            
        except Exception as e:
            print(f"   ❌ {name}: {str(e)[:50]}")
    
    return False

if __name__ == "__main__":
    analyze_encrypted_content()
    try_derived_keys()
