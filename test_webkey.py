"""
1. Test web key (aa4uCch7CR8KiBdQ) for AES decrypt with many IV combinations.
2. Try the web JS CryptoJS decrypt pattern on actual chapter content.
3. Scan .text section (6.3MB) for AES key with stride=1 and cross-validation.
"""
import sys, base64, hmac, hashlib, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from Crypto.Cipher import AES

def get_chapter_data(cid):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{cid}', timeout=15)
    d = r.json()
    if 'data' not in d: return None
    chap = d['data']
    content_str = chap.get('content','')
    if not content_str: return None
    pad = '=' * (-len(content_str) % 4)
    outer = base64.b64decode(content_str + pad)
    sep = b'","value":"'
    p2 = outer.find(sep); vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv_raw = outer[7:p2]
    val_b64 = outer[vs:ct_end]
    mac_s = outer.find(b'"mac":"'); mac_e = outer.find(b'"', mac_s+7)
    mac_hex = outer[mac_s+7:mac_e].decode('ascii')
    ct = base64.b64decode(val_b64 + b'==')
    return {'iv_raw': iv_raw, 'val_b64': val_b64, 'mac_hex': mac_hex,
            'ct': ct, 'ct_last': ct[-16:], 'ct_prev': ct[-32:-16],
            'book_id': chap.get('book_id'), 'content_str': content_str}

c1 = get_chapter_data(21589884)
print(f'c1: book={c1["book_id"]} mac={c1["mac_hex"][:20]} ct={len(c1["ct"])}B')
print(f'    iv_raw({len(c1["iv_raw"])}B): {c1["iv_raw"].hex()}')

# ============================================================
# Part 1: Test web key + many IV/key variants
# ============================================================
print('\n=== Testing web key aa4uCch7CR8KiBdQ with many formulas ===')
web_key_str = 'aa4uCch7CR8KiBdQ'
web_key = web_key_str.encode('ascii')  # 16 bytes

iv_raw = c1['iv_raw']
val_b64 = c1['val_b64']
mac_hex = c1['mac_hex']
ct = c1['ct']

def try_mac(key_bytes, data, mac):
    h = hmac.new(key_bytes, data, hashlib.sha256).hexdigest()
    return h == mac

def try_decrypt(key_bytes, iv_bytes, ct_bytes):
    """Try AES-CBC decrypt and check for valid UTF-8."""
    try:
        dec = AES.new(key_bytes, AES.MODE_CBC, iv_bytes).decrypt(ct_bytes)
        pv = dec[-1]
        if 1 <= pv <= 16 and all(b == pv for b in dec[-pv:]):
            pt = dec[:-pv]
            try:
                text = pt.decode('utf-8')
                return text[:80]
            except:
                pass
    except:
        pass
    return None

# Test MAC with many formulas
print('MAC tests (web key):')
tests = [
    ('iv_raw+val', iv_raw + val_b64),
    ('val_only', val_b64),
    ('b64(iv)+val', base64.b64encode(iv_raw) + val_b64),
    ('hex(iv)+val', iv_raw.hex().encode() + val_b64),
    ('iv[-16:]+val', iv_raw[-16:] + val_b64),
    ('iv[:16]+val', iv_raw[:16] + val_b64),
    ('val+iv_raw', val_b64 + iv_raw),
]
for name, data in tests:
    match = try_mac(web_key, data, mac_hex)
    if match:
        print(f'  *** MAC MATCH: formula={name}, key={web_key_str!r}')
    else:
        h = hmac.new(web_key, data, hashlib.sha256).hexdigest()
        print(f'  no match: {name}: expected {mac_hex[:16]}, got {h[:16]}')

# Also try MD5 of web key as AES key
import hashlib as _hs
for kname, k in [
    ('web_key raw', web_key),
    ('md5(web_key)', _hs.md5(web_key).digest()),
    ('sha256(web_key)', _hs.sha256(web_key).digest()),
    ('sha256(web_key)[:16]', _hs.sha256(web_key).digest()[:16]),
    ('web_key padded 32', web_key + web_key),  # repeat 16+16=32
    ('web_key||web_key', web_key + web_key),
]:
    m = try_mac(k, iv_raw + val_b64, mac_hex)
    if m:
        print(f'  *** MAC MATCH with key={kname}')

# Test AES decrypt with web_key and ALL IV candidates
print('\nAES decrypt tests (web key, various IVs):')
iv_candidates = {
    'iv_raw[:16]': iv_raw[:16],
    'iv_raw[-16:]': iv_raw[-16:],
    'zeros': bytes(16),
    'iv_raw[8:24]': iv_raw[8:24] if len(iv_raw)>=24 else None,
    'b64dec(iv_raw[-24:])': None,
    'iv_last_b64dec': None,
}

# Try base64 decoding the last part of iv_raw
for end_len in [20, 22, 24]:
    tail = iv_raw[-end_len:]
    try:
        pad = '=' * (-len(tail) % 4)
        decoded = base64.b64decode(tail + pad.encode())
        name = f'b64dec(iv_raw[-{end_len}:])={len(decoded)}B'
        if len(decoded) >= 16:
            iv_candidates[name] = decoded[:16]
    except: pass

for name, iv in iv_candidates.items():
    if iv is None: continue
    result = try_decrypt(web_key, iv, ct)
    if result:
        print(f'  *** DECRYPTED with key=web_key, iv={name}: {result[:60]}')
    else:
        print(f'  not valid: iv={name}')

# ============================================================
# Part 2: Explore web API to find content format
# ============================================================
print('\n=== Checking web (vtruyen.com) API ===')
# Check if there's a web API that returns decrypted content or different format
web_urls = [
    'https://vtruyen.com/api/chapters/21589884',
    'https://metruyencv.com/api/chapters/21589884',
    'https://android.lonoapp.net/api/books/139039/chapters?limit=3',
    'https://android.lonoapp.net/api/books/139039',
]
for url in web_urls:
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        print(f'  {url}: {r.status_code}')
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict):
                if 'data' in d:
                    dat = d['data']
                    if isinstance(dat, dict):
                        # Check for key fields
                        for f in ['key', 'decrypt_key', 'secret', 'cipher', 'content_key']:
                            if f in dat:
                                print(f'    FOUND FIELD: {f}={dat[f]}')
                        content = dat.get('content','')
                        if content:
                            print(f'    content (first 60): {content[:60]}')
    except Exception as e:
        print(f'  {url}: ERROR {e}')

print('\nDone.')
