import base64
import json
import re
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def brute_force():
    sample_file = Path(r"extract\novels\Chiến Lược Gia Thiên Tài\Chương 1.txt")
    with open(sample_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        encrypted_content = lines[2].strip() if len(lines) > 2 else ""

    encrypted_content += "=" * ((4 - len(encrypted_content) % 4) % 4)
    raw_decoded = base64.b64decode(encrypted_content)

    print("Raw decoded length:", len(raw_decoded))
    iv_start = raw_decoded.find(b'"iv":"') + 6
    iv_end = raw_decoded.find(b'"', iv_start)
    raw_iv = raw_decoded[iv_start:iv_end]

    val_start = raw_decoded.find(b'"value":"') + 9
    val_end = raw_decoded.find(b'"', val_start)
    raw_val = raw_decoded[val_start:val_end]

    print("Raw IV bytes:", raw_iv)
    
    # Python b64decode ignores garbage characters! Let's see if it gives 16 bytes.
    # Actually let's just keep valid base64 characters.
    valid_b64 = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    clean_iv = bytes([b for b in raw_iv if b in valid_b64])
    clean_val = bytes([b for b in raw_val if b in valid_b64])
    
    print("Clean IV string:", clean_iv)
    iv = base64.b64decode(clean_iv)
    print("IV length:", len(iv))
    
    encrypted_value = base64.b64decode(clean_val)
    print("Value length:", len(encrypted_value))
    
    # now let's try keys
    strings_file = Path("libapp_strings.txt")
    content = strings_file.read_text(encoding='utf-8', errors='ignore')
    
    b64_pattern = re.compile(r'[A-Za-z0-9+/]{43}=|[A-Za-z0-9+/]{42}==|[A-Za-z0-9+/]{44}')
    candidates = set(b64_pattern.findall(content))
    str_pattern32 = re.compile(r'[A-Za-z0-9_!@#$%^&*(){}\[\]\-|~+=\\:;\"\'<>,.?/]{32}')
    candidates.update(str_pattern32.findall(content))
    
    print(f"Testing {len(candidates)} candidates...")
    for cand in candidates:
        keys_to_try = []
        if len(cand) == 44:
            try: keys_to_try.append(base64.b64decode(cand))
            except: pass
        if len(cand) == 32:
            keys_to_try.append(cand.encode('utf-8'))
            
        for key in keys_to_try:
            if len(key) == 32:
                try:
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    dec = unpad(cipher.decrypt(encrypted_value), AES.block_size)
                    print("✅ FOUND KEY:", cand)
                    print(dec.decode('utf-8')[:200])
                    return
                except:
                    pass
    print("❌ No key found")

if __name__ == '__main__':
    brute_force()
