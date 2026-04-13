"""
Test AES decrypt with FIXED iv extraction (7 bytes prefix, not 8).
Format: {"iv":"<XX bytes>","value":"<b64>"}
  - '{"iv":"' = 7 bytes (positions 0-6)  
  - iv value starts at position 7
"""
import requests, base64, sys, hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import urllib3; urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

PROXY = {'https': 'http://127.0.0.1:8081'}

def fetch_chapter_raw(ch_id):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{ch_id}',
                     verify=False, proxies=PROXY, timeout=15)
    content = r.json()['data']['content']
    try: outer = base64.b64decode(content)
    except: outer = base64.b64decode(content + '==')
    
    # Show raw structure
    prefix = outer[:7]  # {"iv":"
    sep = b'","value":"'
    pos = outer.find(sep)
    
    # Fixed: iv starts at position 7 (after {"iv":")
    iv_field = outer[7:pos]
    ct_b64_bytes = outer[pos + len(sep):-2]  # trim trailing "}
    ct = base64.b64decode(ct_b64_bytes + b'==')
    
    return prefix, iv_field, ct, outer

print("=== Fetching chapters and analyzing ===")
chapters = {}
for ch_id in [21589884, 21598093, 21647009]:
    prefix, iv_field, ct, outer = fetch_chapter_raw(ch_id)
    print(f"\nChapter {ch_id}:")
    print(f"  prefix={prefix} ({len(prefix)} bytes)")
    print(f"  iv_field: {len(iv_field)} bytes = {iv_field.hex()}")
    print(f"  iv_field[:16]: {iv_field[:16].hex()}")
    print(f"  ct: {len(ct)} bytes (mod16={len(ct)%16})")
    chapters[ch_id] = (iv_field, ct)

def try_aes(ct, iv, key):
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv[:16])
        raw = cipher.decrypt(ct)
        unpadded = unpad(raw, 16)
        text = unpadded.decode('utf-8')
        return text
    except:
        return None

def is_vietnamese(text):
    if not text or len(text) < 30: return False
    vi = 'àáâãèéêìíòóôõùúăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ'
    return sum(1 for c in text if c.lower() in vi) > 8

# Generate key candidates
keys = {}

# Hashes of strings
for s in ['lonoapp', 'novelfever', 'LonOApp', 'novel.fever', 'lonoapp2024',
          'lonoapp2025', 'android.lonoapp.net', 'secret', 'app.lono',
          'lonoappkey', 'novelappkey', 'lono_secret', 'lono_key',
          'bookapp', 'reading', 'book_secret', 'chapter_key', 'encrypt_key',
          'aes_key', 'data_key', 'content_key', 'book_encrypt', 'app_secret',
          '', '0', '1234567890']:
    keys[f'sha256({s!r})'] = hashlib.sha256(s.encode()).digest()
    keys[f'sha256md5({s!r})'] = hashlib.sha256(hashlib.md5(s.encode()).digest()).digest()
    if len(s) <= 16:
        keys[f'md5x2({s!r})'] = hashlib.md5(s.encode()).digest() * 2

# Fixed 32-byte strings
for s in ['lonoappSecretKey', 'lonoappSecretKey12345678lonoapp!',
          'novelfeverSecretK', '12345678901234567890123456789012',
          'abcdefghijklmnopabcdefghijklmnop']:
    keys[f'utf8_32({s!r})'] = (s.encode() + b'\x00' * 32)[:32]

# Zero, 0xff
keys['zeros'] = b'\x00' * 32
keys['0xff'] = b'\xff' * 32

print(f"\n=== Testing {len(keys)} keys ===")
found_any = False
for key_name, key in keys.items():
    for ch_id, (iv_field, ct) in chapters.items():
        # Try different IV positions
        for iv_offset in [0, 3, 6, 16, 19]:
            iv16 = iv_field[iv_offset:iv_offset+16]
            if len(iv16) != 16:
                continue
            result = try_aes(ct, iv16, key)
            if result and is_vietnamese(result):
                print(f"\n*** MATCH *** key={key_name}, iv_offset={iv_offset}, ch={ch_id}")
                print(f"  key hex: {key.hex()}")
                print(f"  iv hex: {iv16.hex()}")
                print(f"  result[:200]: {result[:200]}")
                found_any = True

if not found_any:
    print("No matches found.")
    
    # Print some samples to debug
    print("\n=== Decryption samples (zeros key, different IVs) ===")
    ch_id = 21589884
    iv_field, ct = chapters[ch_id]
    zero_key = b'\x00' * 32
    for offset in range(0, len(iv_field)-15, 4):
        iv16 = iv_field[offset:offset+16]
        try:
            cipher = AES.new(zero_key, AES.MODE_CBC, iv16)
            raw = cipher.decrypt(ct[:64])
            print(f"  iv_offset={offset}: {raw[:32].hex()} | {raw[:32]!r}")
        except:
            pass
