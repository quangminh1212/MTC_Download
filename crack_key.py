"""
Use MAC = HMAC-SHA256(iv_field + value_field, key) to crack the key.
1. Extract all printable-ASCII strings from libapp.so (len 16-64)
2. For each, test raw_key, base64_decoded, md5, sha256 variants against MAC
3. Also test all x1 rotations (properly extracted)
"""
import sys, base64, hmac, hashlib, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from Crypto.Cipher import AES
import requests

# Get fresh API data
print('Fetching chapter 21589884...')
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content_str = r.json()['data']['content']
pad = '=' * (-len(content_str) % 4)
outer = base64.b64decode(content_str + pad)

sep = b'","value":"'
p2 = outer.find(sep)
vs = p2 + len(sep)
ct_end = outer.find(b'"', vs)
iv_raw = outer[7:p2]
val_b64 = outer[vs:ct_end]
mac_s = outer.find(b'"mac":"')
mac_e = outer.find(b'"', mac_s + 7)
mac_hex = outer[mac_s+7:mac_e].decode('ascii')
ct = base64.b64decode(val_b64 + b'==')

print(f'iv_raw {len(iv_raw)}B = {iv_raw.hex()}')
print(f'val_b64 {len(val_b64)}B')
print(f'mac = {mac_hex}')
print(f'ct = {len(ct)}B')

# The MAC data: try multiple forms
def mac_data_forms(iv_raw, val_b64):
    return {
        'raw_iv': iv_raw + val_b64,                          # raw iv + b64 value
        'b64_iv': base64.b64encode(iv_raw) + val_b64,       # b64(iv) + b64 value  
        'b64_iv16': base64.b64encode(iv_raw[:16]) + val_b64, # b64(first 16B) + b64 value
        'iv16_raw': iv_raw[:16] + val_b64,                   # first 16B + b64 value
    }

def check_key(k_bytes, iv_raw, val_b64, expected_mac):
    forms = mac_data_forms(iv_raw, val_b64)
    for form_name, data in forms.items():
        h = hmac.new(k_bytes, data, hashlib.sha256).hexdigest()
        if h == expected_mac:
            return form_name
    return None

def check_decrypt(k_bytes, iv_raw, ct):
    for iv_variant in [iv_raw[:16], iv_raw[:16], bytes(16)]:
        try:
            c = AES.new(k_bytes, AES.MODE_CBC, iv_variant[:16])
            pt = c.decrypt(ct)
            pv = pt[-1]
            if 1 <= pv <= 16 and all(b == pv for b in pt[-pv:]):
                try:
                    text = pt[:-pv].decode('utf-8')[:60]
                    return text
                except: pass
        except: pass
    return None

def test_key_variants(k_bytes_or_str, label):
    """Test multiple key variants for a given raw bytes or string."""
    if isinstance(k_bytes_or_str, str):
        k_bytes_or_str = k_bytes_or_str.encode('utf-8', errors='replace')
    
    to_test = {}
    b = k_bytes_or_str
    if len(b) in (16, 24, 32):
        to_test[f'{label}(raw{len(b)})'] = b
    if len(b) >= 16:
        to_test[f'{label}(md5)'] = hashlib.md5(b).digest()
    if len(b) >= 16:
        to_test[f'{label}(sha256)'] = hashlib.sha256(b).digest()
    # Try base64 decode if possible
    try:
        bd = base64.b64decode(b + b'=' * (-len(b) % 4))
        if len(bd) in (16, 24, 32):
            to_test[f'{label}(b64dec{len(bd)})'] = bd
    except: pass
    
    for name, kb in to_test.items():
        mac_form = check_key(kb, iv_raw, val_b64, mac_hex)
        if mac_form:
            print(f'  MAC MATCH: {name} key={kb.hex()} form={mac_form!r} key_str={kb!r}')
        pt = check_decrypt(kb, iv_raw, ct)  
        if pt:
            print(f'  DECRYPT: {name} key={kb.hex()} -> {pt!r}')

# ---- 1. x1 rotations (fix extraction) ----
print('\n=== x1 rotations ===')
with open('app_bundle.js', encoding='utf-8') as f:
    js = f.read()

# Find x1 array
x1_pos = js.find("function x1(){")
bracket_pos = js.index('[', x1_pos)
# Depth tracker (string-aware)
depth = 0; in_str = False; esc = False; i_end = None
for idx in range(bracket_pos, len(js)):
    c = js[idx]
    if esc: esc = False; continue
    if in_str:
        if c == '\\': esc = True
        elif c == in_str: in_str = False
        continue
    if c in ('"', "'"): in_str = c; continue
    if c == '[': depth += 1
    elif c == ']':
        depth -= 1
        if depth == 0: i_end = idx; break
arr_str = js[bracket_pos:i_end+1]
# Try single-quoted first, then double-quoted
entries = re.findall(r"'((?:[^'\\]|\\.)*)'", arr_str)
if len(entries) < 50:
    entries = re.findall(r'"((?:[^"\\]|\\.)*)"', arr_str)
print(f'x1 entries: {len(entries)}')

# Build keys: a0(149) + "ch7CR" + a0(224) + "Q" at various rotations
found = False
for k in range(len(entries)):
    N = len(entries)
    e149 = entries[(19 + k) % N]   # a0(149) = x1()[149-130=19]
    e224 = entries[(94 + k) % N]   # a0(224) = x1()[224-130=94]
    key_str = e149 + "ch7CR" + e224 + "Q"
    if len(key_str) not in (16, 24, 32): continue
    test_key_variants(key_str, f'x1_k{k}')

print('Done x1 scan')

# ---- 2. Scan libapp.so for strings ----
print('\n=== libapp.so string scan ===')
import os
lib_path = r'.\libapp_extracted\libapp.so'
if os.path.exists(lib_path):
    with open(lib_path, 'rb') as f:
        lib = f.read()
    print(f'libapp.so: {len(lib)} bytes')
    
    # Find all runs of printable ASCII chars of length 16-64
    count = 0
    for m in re.finditer(rb'[\x20-\x7e]{16,64}(?=[\x00\x01\x02\x03\x04])', lib):
        s = m.group()
        test_key_variants(s, f'lib_{m.start():08x}')
        count += 1
    print(f'Tested {count} strings from libapp.so')
else:
    print('libapp.so not found')

# ---- 3. JS constants / other keys ----
print('\n=== JS: search for other keys (non-x1) ===')
# Look for AES decrypt calls not using x1
aes_calls = list(re.finditer(r'AES[._]+decrypt|decrypt[._]+AES|CryptoJS', js, re.I))
for m in aes_calls[:5]:
    ctx = js[max(0,m.start()-100):m.start()+200]
    print(f'  pos={m.start()}: {ctx[:150]!r}')
    print()
