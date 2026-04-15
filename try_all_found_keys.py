#!/usr/bin/env python3
"""Thử tất cả các key tìm được từ strings."""
import base64
import json
import re
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

def extract_all_keys():
    """Extract tất cả các key tiềm năng từ strings file."""
    strings_file = Path("libapp_strings.txt")
    if not strings_file.exists():
        print("❌ libapp_strings.txt not found")
        return []
    
    with open(strings_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    keys = set()
    
    # Pattern 1: Hex keys (64 chars = 32 bytes)
    hex_pattern = re.compile(r'[0-9a-fA-F]{64}')
    for match in hex_pattern.findall(content):
        keys.add(('hex', match))
    
    # Pattern 2: Base64-like strings (40-60 chars)
    b64_pattern = re.compile(r'[A-Za-z0-9+/]{40,60}={0,2}')
    for match in b64_pattern.findall(content):
        # Filter out known non-key patterns
        if not any(x in match for x in ['package:', 'dart:', 'init:', 'get:', 'set:', '_']):
            keys.add(('b64', match))
    
    # Pattern 3: Long hex strings (không phải 64 chars)
    long_hex_pattern = re.compile(r'[0-9a-fA-F]{40,80}')
    for match in long_hex_pattern.findall(content):
        if len(match) >= 64:
            # Cắt lấy 64 chars đầu
            keys.add(('hex_trunc', match[:64]))
    
    return list(keys)

def main():
    print("=" * 60)
    print("THỬ TẤT CẢ CÁC KEY TÌM ĐƯỢC")
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
    
    # Extract keys
    print("\nExtracting keys from strings...")
    keys = extract_all_keys()
    print(f"Found {len(keys)} potential keys")
    
    # Also add keys from deep_search output
    additional_hex_keys = [
        "ffffffffffffffffffffffffffffffff6c611070995ad10045841b09b761b893",
        "9b9f605f5a858107ab1ec85e6b41c8aacf846e86789051d37998f7b9022d7598",
        "fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",
        "ffffffff00000001000000000000000000000000ffffffffffffffffffffffff",
        "a9fb57dba1eea9bc3e660a909d838d726e3bf623d52620282013481d1f6e5374",
        "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd97",
        "ffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141",
        "662c61c430d84ea4fe66a7733d0b76b7bf93ebc4af2f49256ae58101fee92b04",
        # Keys from grep results
        "04b199b13b9b34efc1397e64baeb05acc265ff2378add6718b7c7c1961f0991b842443772152c9e0ad",
        "036b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296",
        "04db4ff10ec057e9ae26b07d0280b7f4341da5d1b1eae06c7d9b2f2f6d9c5628a7844163d015be86344082aa88d95e2f9d",
        "617fab6832576cbbfed50d99f0249c3fee58b94ba0038c7ae84c8c832f2c",
        "2580f63ccfe44138870713b1a92369e33e2135d266dbb372386c400b",
        "048bd2aeb9cb7e57cb2c4b482ffc81b7afb9de27e1e3bd23c23a4453bd9ace3262547ef835c3dac4fd97f8461a14611dc9c27745132ded8e545c1d54c72f046997",
        "c302f41d932a36cda7a3463093d18db78fce476de1a86294",
        "c469684435deb378c4b65ca9591e2a5763059a2e",
        "64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1",
        "100000000000000000000351ee786a818f3a1a16b",
        "e8b4011604095303ca3b8099982be09fcb9ae616",
        "04aa87ca22be8b05378eb1c71ef320ad746e1d3b628ba79b9859f741e082542a385502f25dbf55296c3a545e3872760ab73617de4a96262c6f5d9e98bf9292dc29f8f41dbd289a147ce9da3113b5f0b8c00a60b1ce1d7e819d7a431d7c90ea0e5f",
        "044a96b5688ef573284664698968c38bb913cbfc8223a628553168947d59dcc912042351377ac5fb32",
        "04188da80eb03090f67cbf20eb43a18800f4ff0afd82ff101207192b95ffc8da78631011ed6b24cdd573f977a11e794811",
        "d7c134aa264366862a18302575d1d787b09f075797da89f57ec8c0ff",
        "020ffa963cdca8816ccc33b8642bedf905c3d358573d3f27fbbd3b3cb9aaaf",
        "c302f41d932a36cda7a3463093d18db78fce476de1a86297",
        "469a28ef7c28cca3dc721d044f4496bcca7ef4146fbf25c9",
        "04a1455b334df099df30fc28a169a467e9e47075a90f7e650eb6b7a45c7e089fed7fba344282cafbd6f7e319f7c0b0bd59e2ca4bdb556d61a5",
        "e95e4a5f737059dc60dfc7ad95b3d8139515620f",
        "044ba30ab5e892b4e1649dd0928643adcd46f5882e3747def36e956e97",
        "aadd9db8dbe9c48b3fd4e6ae33c9fc07cb308db3b3c9d20ed6639cca703308717d4d9b009bc66842aecda12ae6a380e62881ff2f2d82c68528aa6056583a48f3",
    ]
    
    for key in additional_hex_keys:
        keys.append(('hex_add', key))
    
    # Remove duplicates
    unique_keys = set()
    for key_type, key_value in keys:
        unique_keys.add((key_type, key_value))
    
    keys = list(unique_keys)
    print(f"Total unique keys to test: {len(keys)}")
    
    # Test each key
    print("\n" + "=" * 60)
    print("TESTING KEYS...")
    print("=" * 60)
    
    tested = 0
    for key_type, key_value in keys:
        tested += 1
        if tested % 50 == 0:
            print(f"Progress: {tested}/{len(keys)}...")
        
        # Convert to bytes
        key_bytes = None
        
        if key_type.startswith('hex'):
            # Hex string
            if len(key_value) >= 64:
                try:
                    key_bytes = bytes.fromhex(key_value[:64])
                except:
                    continue
        elif key_type == 'b64':
            # Base64 string
            try:
                # Pad if needed
                padded = key_value + '=' * ((4 - len(key_value) % 4) % 4)
                key_bytes = base64.b64decode(padded)
            except:
                continue
        
        if not key_bytes or len(key_bytes) != 32:
            continue
        
        # Try as base64 key
        app_key = 'base64:' + base64.b64encode(key_bytes).decode()
        
        result = decrypt_laravel(encrypted_content, app_key)
        
        if result and len(result) > 100:
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS!")
            print(f"{'='*60}")
            print(f"Key type: {key_type}")
            print(f"Key value: {key_value}")
            print(f"APP_KEY: {app_key}")
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
                f.write(app_key)
            
            print(f"✅ Key saved to: {key_file}")
            return
    
    print(f"\n{'='*60}")
    print(f"❌ Tested {tested} keys, none worked")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("1. Use mitmproxy to capture traffic")
    print("2. Use Frida to hook decrypt function")
    print("3. Decompile Dart code with reFlutter")

if __name__ == "__main__":
    main()
