"""Deep scan of metruyencv.com JS bundle for AES key."""
import requests, re, base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Fetch chapter CT
r0 = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content = r0.json()['data']['content']
outer = base64.b64decode(content + '==')
sep = b'","value":"'
pos = outer.find(sep); vs = pos + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')
print(f'CT length: {len(ct)}, IV: {iv16.hex()}')

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

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}

# Download the JS
js_url = 'https://metruyencv.com/build/assets/app-ed2d0a7f.js'
print(f'\nFetching {js_url}...')
r = requests.get(js_url, timeout=30, headers=HEADERS)
print(f'HTTP {r.status_code}, size {len(r.text)}')
js = r.text

# Look for AES context
print('\n--- AES context ---')
for m in re.finditer(r'.{0,100}[aA][eE][sS].{0,100}', js):
    ctx = m.group()
    if 'encrypt' in ctx.lower() or 'decrypt' in ctx.lower() or 'key' in ctx.lower():
        print(' ', ctx[:200])
        print()

# Look for hex keys of right lengths
print('\n--- Hex strings (32, 48, 64 chars) ---')
hex_found = set()
for m in re.finditer(r'["\']([0-9a-fA-F]{32})["\']', js):
    hex_found.add(m.group(1).lower())
for m in re.finditer(r'["\']([0-9a-fA-F]{48})["\']', js):
    hex_found.add(m.group(1).lower())
for m in re.finditer(r'["\']([0-9a-fA-F]{64})["\']', js):
    hex_found.add(m.group(1).lower())

print(f'Hex strings found: {len(hex_found)}')
for h in list(hex_found)[:50]:
    k = bytes.fromhex(h)
    ok = check_strict(k)
    print(f'  {h} -> {"FOUND!" if ok else "no"}')
    if ok: print(f"*** KEY: {h} ***")

# Look for base64 key material (24, 32, 44 chars)
print('\n--- Base64 strings (24, 32, 44 chars) ---')
b64_keys = set()
for n in [24, 32, 44]:
    for m in re.finditer(r'["\']([A-Za-z0-9+/]{' + str(n) + r'}={0,2})["\']', js):
        b64_keys.add(m.group(1))

print(f'B64 strings found: {len(b64_keys)}')
for b in list(b64_keys)[:50]:
    for pad in ['', '=', '==']:
        try:
            k = base64.b64decode(b + pad)
            if len(k) in (16,24,32):
                ok = check_strict(k)
                print(f'  {b!r} -> {k.hex()} -> {"FOUND!" if ok else "no"}')
                if ok: print(f"*** KEY: {k.hex()} ***")
                break
        except: pass

# JWT-style tokens (look for "Bearer" or authorization)
print('\n--- Auth/key-like assignments ---')
for m in re.finditer(r'(?:key|Key|KEY|secret|Secret|token|cipher|encrypt|decrypt)\s*[=:]\s*["\']([^"\']{8,64})["\']', js):
    val = m.group(1)
    ctx = js[max(0,m.start()-30):m.end()+30]
    print(f'  Match: {ctx[:120]}')
    # Try as UTF-8 key
    k = val.encode('utf-8')
    if len(k) in (16,24,32):
        ok = check_strict(k)
        print(f'    direct utf8: {k.hex()} -> {"FOUND!" if ok else "no"}')
    # Try as hex
    if re.match(r'^[0-9a-fA-F]{32,64}$', val) and len(val) in (32,48,64):
        try:
            k = bytes.fromhex(val)
            ok = check_strict(k)
            print(f'    hex: {k.hex()} -> {"FOUND!" if ok else "no"}')
        except: pass
    # Try as b64
    for pad in ['', '=', '==']:
        try:
            k = base64.b64decode(val + pad)
            if len(k) in (16,24,32):
                ok = check_strict(k)
                print(f'    b64: {k.hex()} -> {"FOUND!" if ok else "no"}')
        except: pass

# Look for fromWordArray/CryptoJS pattern
print('\n--- CryptoJS / fromWordArray patterns ---')
for pat in ['fromHex', 'fromBase64', 'fromWordArray', 'fromUtf8', 'words:', 'sigBytes:', 'parseKey', 'iv:', 'key:']:
    if pat in js:
        for m in re.finditer(re.escape(pat) + r'.{0,150}', js):
            print(f'  [{pat}]: {m.group()[:200]}')
