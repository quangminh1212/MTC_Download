"""
Compare mobile vs web API content formats and test key/IV variants.
The JS window.decrypt uses: iv = CryptoJS.enc.Utf8.parse(n) (same as key!)
But mobile API returns {"iv":"...","value":"..."} format.
"""
import sys, base64, json, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

KEY_STR = 'aa4uCch7CR8KiBdQ'
KEY_BYTES = KEY_STR.encode('utf-8')  # 16 bytes
CHAPTER_ID = 21589884

# ---- Test 1: Fetch from WEB API ----
print('=== WEB API: api.lonoapp.net ===')
try:
    r1 = requests.get(f'https://api.lonoapp.net/api/chapters/{CHAPTER_ID}',
                      headers={'User-Agent': 'Mozilla/5.0'},
                      timeout=15)
    print(f'Status: {r1.status_code}')
    if r1.status_code == 200:
        d1 = r1.json()
        c1 = d1['data']['content'] if 'data' in d1 else d1.get('content', '')
        print(f'Content type: {type(c1).__name__}, len={len(str(c1))}')
        print(f'Content (first 200): {str(c1)[:200]!r}')
    else:
        print(f'Headers: {dict(r1.headers)}')
        print(f'Body: {r1.text[:500]}')
except Exception as e:
    print(f'Error: {e}')

# ---- Test 2: Fetch from MOBILE API ----
print('\n=== MOBILE API: android.lonoapp.net ===')
r2 = requests.get(f'https://android.lonoapp.net/api/chapters/{CHAPTER_ID}', timeout=15)
d2 = r2.json()
content_mobile = d2['data']['content']
outer = base64.b64decode(content_mobile + '==')
print(f'outer ({len(outer)}B) first 100: {outer[:100]!r}')

# Find separator
sep = b'","value":"'
p2 = outer.find(sep)
vs = p2 + len(sep)
ct_end = outer.find(b'"', vs)
print(f'p2={p2}, vs={vs}, ct_end={ct_end}')
print(f'IV region outer[7:{p2}] ({p2-7}B): {outer[7:p2].hex()} = {outer[7:p2]!r}')

ct_b64 = outer[vs:ct_end]
ct = base64.b64decode(ct_b64 + b'==')
print(f'CT: {len(ct)}B, last 32: {ct[-32:].hex()}')
print(f'CT len % 16 = {len(ct) % 16}')

# ---- Test 3: Try key with ALL reasonable IV options ----
print(f'\n=== Testing key={KEY_STR!r} with various IVs ===')

def decrypt_attempt(tag, kb, iv_bytes):
    try:
        # Direct decrypt without padding check first
        pt_raw = AES.new(kb, AES.MODE_CBC, iv_bytes).decrypt(ct)
        # Check padding
        pv = pt_raw[-1]
        if 1 <= pv <= 16 and all(pt_raw[-i] == pv for i in range(1, pv+1)):
            pt = pt_raw[:-pv].decode('utf-8')
            viet = ['chương','không','người','trong','được']
            sc = sum(pt.lower().count(w) for w in viet)
            print(f'  VALID ({tag}): score={sc}, first 100={pt[:100]!r}')
            return kb
        else:
            # Show last block plaintext for debugging
            last_plain = pt_raw[-16:]
            print(f'  BAD_PAD ({tag}): last_block={last_plain.hex()} pv={pv}')
    except Exception as e:
        print(f'  ERROR ({tag}): {e}')
    return None

IV_VARIANTS = [
    ('key_as_iv_16B',  KEY_BYTES),                         # key == iv (web JS style)
    ('raw_7_23',       outer[7:23]),                       # 16 raw bytes at offset 7
    ('zero_iv',        b'\x00' * 16),
    ('hardcoded_iv',   b'TgB9xWmKqY71RdNc'),               # IV from JS array
]

# If iv region is 22 bytes, maybe it's base64-encoded standard IV
iv_field_bytes = outer[7:p2]
print(f'\niv_field_bytes ({len(iv_field_bytes)}B): {iv_field_bytes.hex()}')
# Try base64-decoding the printable part
try:
    iv_b64 = base64.b64decode(iv_field_bytes + b'==')
    print(f'iv_b64 decoded ({len(iv_b64)}B): {iv_b64.hex()}')
    IV_VARIANTS.append(('b64_iv_field', iv_b64[:16] if len(iv_b64) >= 16 else (iv_b64 + b'\x00'*16)[:16]))
except: pass

# The iv might be: first 16 bytes of iv_field (after stripping the 'SA==' part that's base64 padding)
# "oO+bol\xbb}0\"C|\x96l-\xbb\x95\xde1Bng4AEzt8BmofSA=="
# Maybe SA== is the end of actual base64 data and the raw string includes extra char
# Let's try treating the bytes that appear to be base64 chars as base64
import re
printable_base64_chars = re.sub(b'[^A-Za-z0-9+/=]', b'', iv_field_bytes)
print(f'printable_b64 ({len(printable_base64_chars)}B): {printable_base64_chars}')
try:
    iv_from_printable = base64.b64decode(printable_base64_chars + b'==')
    print(f'printable b64 decoded ({len(iv_from_printable)}B): {iv_from_printable.hex()}')
    IV_VARIANTS.append(('printable_b64_iv', iv_from_printable[:16]))
except Exception as e:
    print(f'printable b64 error: {e}')

for tag, iv in IV_VARIANTS:
    if len(iv) != 16:
        print(f'  SKIP ({tag}): iv len={len(iv)} (need 16)')
        continue
    decrypt_attempt(tag, KEY_BYTES, iv)

# ---- Test: Maybe the mobile content ct is in WEB format (no iv in content) ----
print(f'\n=== Test: treat outer as pure base64 CT (web format) ===')
# outer itself might be the ciphertext with no iv wrapper
try:
    ct2 = outer
    iv2 = KEY_BYTES  # key = iv
    pt_raw = AES.new(KEY_BYTES, AES.MODE_CBC, iv2).decrypt(ct2[:len(ct2)-(len(ct2)%16)])
    pv = pt_raw[-1]
    print(f'outer as CT: pv={pv}, last_block={pt_raw[-16:].hex()}')
except Exception as e:
    print(f'  Error: {e}')
