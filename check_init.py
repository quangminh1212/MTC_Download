"""Inspect /api/init response and other endpoint responses for key material."""
import requests, json, base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Fetch chapter CT for verification
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content = r.json()['data']['content']
outer = base64.b64decode(content + '==')
sep = b'","value":"'
pos = outer.find(sep); vs = pos + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')

def check_strict(key_bytes):
    try:
        if len(key_bytes) not in (16,24,32): return False
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
        pv = lp[-1]
        if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): return False
        pt = unpad(AES.new(key_bytes, AES.MODE_CBC, iv16).decrypt(ct), 16)
        t = pt.decode('utf-8')
        viet = ['chương','không','người','trong','được']
        return sum(t.lower().count(w) for w in viet) >= 3
    except: return False

# Fetch /api/init
print('=== /api/init responses ===')
for base_url in ['https://android.lonoapp.net/api', 'https://api.lonoapp.net/api']:
    r_init = requests.get(f'{base_url}/init', 
                          headers={'User-Agent':'okhttp/4.9.1'}, timeout=10)
    print(f'\n{base_url}/init:')
    print(json.dumps(r_init.json(), indent=2, ensure_ascii=False))

print()
# Check any string values in init that look like base64 or hex keys
def find_key_candidates(obj, path=''):
    if isinstance(obj, str) and len(obj) in range(20, 65):
        # Try as base64 key
        for pad in [b'', b'=', b'==']:
            try:
                k = base64.b64decode(obj.encode() + pad)
                if len(k) in (16,24,32):
                    ok = check_strict(k)
                    print(f'  {path}: b64({obj!r}) -> {k.hex()} -> {"FOUND!" if ok else "no"}')
                    if ok: return k
            except: pass
        # Try as hex key  
        if all(c in '0123456789abcdefABCDEF' for c in obj):
            for n in (32,48,64):
                if len(obj) == n:
                    try:
                        k = bytes.fromhex(obj)
                        ok = check_strict(k)
                        print(f'  {path}: hex({obj!r}) -> {k.hex()} -> {"FOUND!" if ok else "no"}')
                        if ok: return k
                    except: pass
    elif isinstance(obj, dict):
        for key, val in obj.items():
            r2 = find_key_candidates(val, f'{path}.{key}')
            if r2: return r2
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            r2 = find_key_candidates(v, f'{path}[{i}]')
            if r2: return r2
    return None

for base_url in ['https://android.lonoapp.net/api']:
    r_init = requests.get(f'{base_url}/init', headers={'User-Agent':'okhttp/4.9.1'}, timeout=10)
    print(f'Scanning {base_url}/init for key candidates:')
    result = find_key_candidates(r_init.json())
    if result:
        print(f'KEY FOUND: {result.hex()}')
