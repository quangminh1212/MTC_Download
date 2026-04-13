"""
Comprehensive AES decrypt test.
Structure: outer_base64 -> bytes -> {"iv":"<35 raw bytes>","value":"<b64 ciphertext>"}
- iv_bytes[:16] = actual AES-CBC IV (16 bytes)
- value = base64 ciphertext
- Key is 32 bytes (AES-256-CBC), hardcoded in app
"""
import requests, base64, sys, hashlib, os, re
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import urllib3; urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

PROXY = {'https': 'http://127.0.0.1:8081'}

def fetch_chapter(ch_id):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{ch_id}',
                     verify=False, proxies=PROXY, timeout=15)
    content = r.json()['data']['content']
    try: outer = base64.b64decode(content)
    except: outer = base64.b64decode(content + '==')
    
    sep = b'","value":"'
    pos = outer.find(sep)
    iv_bytes = outer[8:pos]
    ct_b64 = outer[pos + len(sep):-2].decode('ascii')  # trim last "}
    ct = base64.b64decode(ct_b64 + '==')
    return iv_bytes, ct

def try_decrypt(ct, iv, key):
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw = cipher.decrypt(ct)
        unpadded = unpad(raw, 16)
        text = unpadded.decode('utf-8')
        return text
    except Exception:
        return None

def is_vietnamese(text):
    if len(text) < 50:
        return False
    # Check for common Vietnamese characters
    vi_chars = 'àáâãäåæďèéêëìíîïðñòóôõöùúûüýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ'
    count = sum(1 for c in text if c in vi_chars or c in vi_chars.upper())
    return count > 10

print("Fetching 3 chapters...")
chapters = {}
for ch_id in [21589884, 21598093, 21647009]:
    iv_bytes, ct = fetch_chapter(ch_id)
    iv16 = iv_bytes[:16]  # first 16 bytes as AES IV
    chapters[ch_id] = (iv16, ct)
    print(f"  Chapter {ch_id}: iv16={iv16.hex()}, ct_len={len(ct)}")

print("\n--- Testing key candidates ---")

# Build key list
key_candidates = []

# 1. SHA256 of common strings
for s in ['lonoapp', 'novelfever', 'secret', 'android', 'lonoapp.net',
          'android.lonoapp.net', 'novel', 'app_key', 'lono', 'app',
          'lonoapp_secret', 'lonoapp_key', 'bookapp', 'book_key',
          '1234567890abcdef', 'supersecretkey12', 'lonoapp2024', 'lonoapp2025',
          'lonoapp123', 'novelfever123', 'reading', 'chapter', 'encrypt',
          'aescrypt', 'aes_key', 'flutter', 'dart']:
    key_candidates.append((f'sha256({s!r})', hashlib.sha256(s.encode()).digest()))
    key_candidates.append((f'sha256({s.upper()!r})', hashlib.sha256(s.upper().encode()).digest()))
    key_candidates.append((f'md5x2({s!r})', hashlib.md5(s.encode()).digest() * 2))

# 2. Zero key, all-ones key
key_candidates.append(('zeros', b'\x00' * 32))
key_candidates.append(('ones', b'\xff' * 32))
key_candidates.append(('0102..', bytes(range(32))))

# 3. Fixed strings padded to 32
for s in ['lonoapp', 'novelfever', 'lonoappandroid', 'android.lonoapp']:
    if len(s) <= 32:
        key_candidates.append((f'pad0({s!r})', s.encode().ljust(32, b'\x00')))
        key_candidates.append((f'pad_pkcs({s!r})', s.encode().ljust(32, bytes([32-len(s)]))))

# 4. Try known strings from conversations
for s in ['ZkwwBadroid', 'LzqWorHv', 'lonoappSecretKey12345678']:
    b = s.encode()
    if len(b) == 32:
        key_candidates.append((f'raw({s!r})', b))
    key_candidates.append((f'sha256({s!r})', hashlib.sha256(b).digest()))

print(f"Total key candidates: {len(key_candidates)}")

found = False
for key_name, key in key_candidates:
    for ch_id, (iv16, ct) in chapters.items():
        result = try_decrypt(ct, iv16, key)
        if result and is_vietnamese(result):
            print(f"\n*** FOUND! Key={key_name}, Chapter={ch_id} ***")
            print(f"Key bytes: {key.hex()}")
            print(f"Decrypted preview: {result[:200]}")
            found = True
            break
    if found:
        break

if not found:
    print("None of the candidates worked with iv[:16] as IV")
    
    # Try alternative IV extraction
    print("\n--- Trying alternative IV positions ---")
    for ch_id, (iv16_unused, ct) in chapters.items():
        iv_bytes, _ = fetch_chapter(ch_id)
        for offset in [0, 1, 2, 4, 8, 16, 17, 19]:
            iv_alt = iv_bytes[offset:offset+16]
            if len(iv_alt) != 16:
                continue
            # Try top 5 keys with this iv
            for key_name, key in key_candidates[:20]:
                result = try_decrypt(ct, iv_alt, key)
                if result and is_vietnamese(result):
                    print(f"\n*** FOUND! iv_bytes[{offset}:{offset+16}] key={key_name} ***")
                    print(f"Decrypted: {result[:200]}")
                    found = True
                    break
            if found:
                break

print("\nDone.")
