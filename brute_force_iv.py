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

    iv_start = raw_decoded.find(b'"iv":"') + 6
    iv_end = raw_decoded.find(b'"', iv_start)
    raw_iv = raw_decoded[iv_start:iv_end]

    val_start = raw_decoded.find(b'"value":"') + 9
    val_end = raw_decoded.find(b'"', val_start)
    raw_val = raw_decoded[val_start:val_end]

    encrypted_value = base64.b64decode(raw_val)
    
    iv_candidates = [
        raw_iv[:16],
        raw_iv[-16:],
        raw_iv.replace(b',', b'').replace(b'\x0c', b'').replace(b'\x95', b'').replace(b'\xa4', b'').replace(b'\x1f', b'').replace(b'{', b'').replace(b'\x8f', b'')[:16],
    ]
    
    # Try just standard Laravel empty IV as well
    iv_candidates.append(b'\x00' * 16)
    
    strings_file = Path("libapp_strings.txt")
    content = strings_file.read_text(encoding='utf-8', errors='ignore')
    
    b64_pattern = re.compile(r'[A-Za-z0-9+/]{43}=|[A-Za-z0-9+/]{42}==|[A-Za-z0-9+/]{44}|[A-Za-z0-9+/]{22}==|[A-Za-z0-9+/]{23}=|[A-Za-z0-9+/]{24}')
    candidates = set(b64_pattern.findall(content))
    str_pattern32 = re.compile(r'[A-Za-z0-9_!@#$%^&*(){}\[\]\-|~+=\\:;\"\'<>,.?/]{32}')
    str_pattern16 = re.compile(r'[A-Za-z0-9_!@#$%^&*(){}\[\]\-|~+=\\:;\"\'<>,.?/]{16}')
    candidates.update(str_pattern32.findall(content))
    candidates.update(str_pattern16.findall(content))
    
    print(f"Testing {len(candidates)} string candidates with {len(iv_candidates)} different IVs...")
    
    for cand in candidates:
        keys_to_try = []
        if len(cand) in (44, 24):
            try: keys_to_try.append(base64.b64decode(cand))
            except: pass
        if len(cand) in (32, 16):
            keys_to_try.append(cand.encode('utf-8'))
            
        for key in keys_to_try:
            if len(key) in (16, 32):
                for idx, iv in enumerate(iv_candidates):
                    if len(iv) != 16: continue
                    try:
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                        dec = cipher.decrypt(encrypted_value)
                        try:
                            dec = unpad(dec, AES.block_size)
                        except:
                            pass
                        # Check if valid readable text
                        if b"Ch" in dec or b"ch" in dec or b"*" in dec:
                            text_dec = dec.decode('utf-8', errors='ignore')
                            if sum(1 for c in text_dec if c.isprintable()) > len(text_dec) * 0.8:
                                print(f"✅ FOUND KEY: {cand}")
                                print(f"IV Match Index: {idx}")
                                print(text_dec[:200])
                                return
                    except:
                        pass
    print("❌ No key found")

if __name__ == '__main__':
    brute_force()
