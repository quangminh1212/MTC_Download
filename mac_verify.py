"""
Use MAC = HMAC-SHA256(iv_field + value_field, key) to verify key candidates.
The outer format is: {"iv":"<raw_iv>","value":"<b64_ct>","mac":"<hex_mac>","tag":""}

Strategy:
1. Verify web JS key aa4uCch7CR8KiBdQ
2. Try ALL 171 x1 rotations (different key formulas)
3. Try 32-byte key variants (AES-256-CBC)
4. Try PBKDF2/MD5 derivations
5. Try i0/t1 table at different rotation
"""
import sys, base64, hmac, hashlib, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---- Setup: get content + extract fields ----
def get_content(chid=21589884):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{chid}', timeout=15)
    content_str = r.json()['data']['content']
    pad = '=' * (-len(content_str) % 4)
    outer = base64.b64decode(content_str + pad)
    sep = b'","value":"'
    p2 = outer.find(sep)
    vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv_raw = outer[7:p2]         # raw iv field bytes
    val_b64 = outer[vs:ct_end]   # base64 CT string as bytes
    mac_start = outer.find(b'"mac":"')
    mac_val_e = outer.find(b'"', mac_start + 7)
    mac_hex = outer[mac_start+7:mac_val_e].decode('ascii')
    ct = base64.b64decode(val_b64 + b'==')
    return {'outer': outer, 'iv_raw': iv_raw, 'val_b64': val_b64, 
            'mac_hex': mac_hex, 'ct': ct}

print('Fetching chapter...')
d = get_content()
print(f'iv_raw ({len(d["iv_raw"])}B): {d["iv_raw"][:20].hex()}...')
print(f'val_b64 ({len(d["val_b64"])}B): {d["val_b64"][:30]}...')
print(f'mac = {d["mac_hex"]}')
print(f'ct = {len(d["ct"])} bytes')

def check_mac(key_bytes, iv_raw, val_b64, expected_mac):
    """HMAC-SHA256(iv + value, key) == mac_hex? Try multiple iv forms."""
    results = {}
    # Form 1: iv_raw as bytes directly
    h = hmac.new(key_bytes, iv_raw + val_b64, hashlib.sha256).hexdigest()
    results['raw_concat'] = (h == expected_mac)
    # Form 2: base64(iv_raw) + val_b64
    iv_b64 = base64.b64encode(iv_raw)
    h = hmac.new(key_bytes, iv_b64 + val_b64, hashlib.sha256).hexdigest()
    results['b64_concat'] = (h == expected_mac)
    # Form 3: base64(iv_raw[:16]) + val_b64
    iv16_b64 = base64.b64encode(iv_raw[:16])
    h = hmac.new(key_bytes, iv16_b64 + val_b64, hashlib.sha256).hexdigest()
    results['b64_16_concat'] = (h == expected_mac)
    # Form 4: only the printable ASCII portion of iv + val
    iv_ascii = bytes([b for b in iv_raw if 0x20 <= b < 0x80])
    h = hmac.new(key_bytes, iv_ascii + val_b64, hashlib.sha256).hexdigest()
    results['ascii_concat'] = (h == expected_mac)
    # Form 5: the PHP json_decode would give back the iv_raw string, so HMAC over json structure
    # Actually try: HMAC over the entire outer JSON except mac field
    # Compute what outer looked like before mac was inserted (just iv+value part)
    # Reconstitute: the actual mac in PHP is hash_hmac('sha256', $iv.$value, $key)
    # where $iv is the iv from compact() = the same PHP variable = iv_raw as stored
    return results

def try_decrypt(key_bytes, iv_raw, ct):
    """Try AES-CBC decrypt with raw 16-byte IV."""
    from Crypto.Cipher import AES
    iv16 = iv_raw[:16]
    try:
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv16)
        pt = cipher.decrypt(ct)
        pv = pt[-1]
        if 1 <= pv <= 16 and all(b == pv for b in pt[-pv:]):
            return pt[:-pv].decode('utf-8', errors='strict')[:100]
    except:
        pass
    return None

# ---- Test web JS key ----
print('\n=== Test 1: Web JS key aa4uCch7CR8KiBdQ ===')
key = b'aa4uCch7CR8KiBdQ'
res = check_mac(key, d['iv_raw'], d['val_b64'], d['mac_hex'])
print(f'MAC check: {res}')
pt = try_decrypt(key, d['iv_raw'], d['ct'])
print(f'Decrypt: {pt!r}')

# ---- Test MD5 of web key ----
print('\n=== Test 2: MD5("aa4uCch7CR8KiBdQ") as key ===')
import hashlib
md5_key = hashlib.md5(b'aa4uCch7CR8KiBdQ').digest()
print(f'md5_key: {md5_key.hex()}')
res = check_mac(md5_key, d['iv_raw'], d['val_b64'], d['mac_hex'])
print(f'MAC check: {res}')
pt = try_decrypt(md5_key, d['iv_raw'], d['ct'])
print(f'Decrypt: {pt!r}')

# ---- Test SHA256 of web key (32 bytes for AES-256) ----
print('\n=== Test 3: SHA256("aa4uCch7CR8KiBdQ") as 32-byte key ===')
sha_key = hashlib.sha256(b'aa4uCch7CR8KiBdQ').digest()
print(f'sha_key: {sha_key.hex()}')
res = check_mac(sha_key, d['iv_raw'], d['val_b64'], d['mac_hex'])
print(f'MAC check: {res}')
# Try AES-256-CBC with first 16B
from Crypto.Cipher import AES
cipher = AES.new(sha_key, AES.MODE_CBC, d['iv_raw'][:16])
pt_raw = cipher.decrypt(d['ct'])
print(f'AES-256 pv: {pt_raw[-1]} (need 1-16 for valid padding)')

# ---- Scan ALL x1 rotations for MAC match ----
print('\n=== Test 4: All 171 x1 rotations => MAC match ===')
# Load x1 entries
with open('app_bundle.js', encoding='utf-8') as f:
    js = f.read()
# Find and extract x1 array
import re
m = re.search(r'function x1\(\)\{', js)
pos = m.start()
bracket_start = js.index('[', pos)
# String-aware bracket tracker
depth = 0; in_str = False; esc = False; k = bracket_start
array_end = None
while k < len(js):
    c = js[k]
    if esc: esc = False; k += 1; continue
    if in_str:
        if c == '\\': esc = True
        elif c == in_str: in_str = False
        k += 1; continue
    if c in ('"', "'"): in_str = c; k += 1; continue
    if c == '[': depth += 1
    elif c == ']':
        depth -= 1
        if depth == 0: array_end = k; break
    k += 1
arr_str = js[bracket_start:array_end+1]
entries = re.findall(r"'((?:[^'\\]|\\.)*)'", arr_str)
print(f'  x1 entries: {len(entries)}')

# Build all 16-char key candidates from e(149) + "ch7CR" + e(224) + "Q" at each rotation k
found_any = False
for k in range(171):
    e149 = entries[(19 + k) % 171]   # a0(149) = x1()[49-130=19 -> 149-130=19], rotated
    e224 = entries[(94 + k) % 171]   # a0(224) = x1()[224-130=94], rotated
    key_str = e149 + "ch7CR" + e224 + "Q"
    if len(key_str) != 16: continue
    key_bytes = key_str.encode('utf-8')
    res = check_mac(key_bytes, d['iv_raw'], d['val_b64'], d['mac_hex'])
    if any(res.values()):
        print(f'  MATCH: k={k}, key={key_str!r}, forms={[k for k,v in res.items() if v]}')
        found_any = True
    # Also try decrypt
    pt = try_decrypt(key_bytes, d['iv_raw'], d['ct'])
    if pt:
        print(f'  DECRYPT MATCH: k={k}, key={key_str!r}, pt={pt!r}')
        found_any = True
if not found_any:
    print('  No MAC/decrypt match in any rotation')

# ---- Check: what does HMAC compute for aa4uCch7CR8KiBdQ to see how far off ----
print('\n=== Debug: MAC values for wrong key ===')
key = b'aa4uCch7CR8KiBdQ'
h1 = hmac.new(key, d['iv_raw'] + d['val_b64'], hashlib.sha256).hexdigest()
h2 = hmac.new(key, base64.b64encode(d['iv_raw']) + d['val_b64'], hashlib.sha256).hexdigest()
print(f'Expected MAC: {d["mac_hex"]}')
print(f'raw concat:   {h1}')
print(f'b64 concat:   {h2}')
