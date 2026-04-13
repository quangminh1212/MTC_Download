"""Deep analysis of obfuscated web JS to extract AES key."""
import requests, re, base64, sys, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Fetch chapter CT first
def get_ct():
    for chid in [21589884, 21589885, 21589886, 21589887]:
        try:
            r = requests.get(f'https://android.lonoapp.net/api/chapters/{chid}', timeout=15)
            d = r.json()
            if d.get('data') and d['data'].get('content'):
                content = d['data']['content']
                outer = base64.b64decode(content + '==')
                sep = b'","value":"'
                pos = outer.find(sep); vs = pos + len(sep)
                ct_end = outer.find(b'"', vs)
                iv16 = outer[7:23]
                ct = base64.b64decode(outer[vs:ct_end] + b'==')
                print(f'Got CT from chapter {chid}: {len(ct)}B, IV={iv16.hex()}')
                return iv16, ct
        except Exception as e:
            print(f'Error {chid}: {e}')
    raise RuntimeError("No CT obtained")

iv16, ct = get_ct()

def check_strict(key_bytes, label=''):
    try:
        if len(key_bytes) not in (16,24,32): return False
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
        pv = lp[-1]
        if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): return False
        pt = unpad(AES.new(key_bytes, AES.MODE_CBC, iv16).decrypt(ct), 16)
        t = pt.decode('utf-8')
        viet = ['chuong','khong','nguoi','trong','duoc','la ']
        score = sum(t.lower().encode('ascii','ignore').decode().count(w) for w in viet)
        print(f'  score={score}, preview: {t[:100].encode("ascii","ignore").decode()}')
        return score >= 3
    except: return False

# Test hardcoded IV as key
iv_chars = [84,103,66,57,120,87,109,75,113,89,55,49,82,100,78,99]
key_str = ''.join(chr(c) for c in iv_chars)
print(f'\nHardcoded chars: {key_str!r}')
k = key_str.encode()
ok = check_strict(k, 'hardcoded_str')
if ok: print(f'*** KEY: {k.hex()} ***')

# Download JS
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}
print('\nDownloading JS...')
r = requests.get('https://metruyencv.com/build/assets/app-ed2d0a7f.js', timeout=30, headers=HEADERS)
js = r.text
print(f'JS size: {len(js)}')
with open('app_bundle.js', 'w', encoding='utf-8') as f:
    f.write(js)

# Find all "ch7CR" contexts
print('\n--- FULL ch7CR contexts ---')
for m in re.finditer(r'.{0,400}ch7CR.{0,400}', js):
    print(m.group())
    print('=====')

# Find the decrypt/encrypt functions that contain "ch7CR"
print('\n--- Decrypt function containing ch7CR ---')
for m in re.finditer(r'(?:function|=>|window\[)[^}]{0,800}ch7CR[^}]{0,800}', js):
    print(m.group())
    print('=====')

# Look for string array definitions (the big array at the start of obfuscated JS)
# Typically: var _0x1234=['string1','string2',...]; or similar
print('\n--- String table candidates ---')
big_arrays = re.finditer(r'(?:var\s+_[0-9a-f]+\s*=\s*)?\[(?:"[^"]*",?\s*){20,}\]', js)
for i, m in enumerate(big_arrays):
    start = max(0, m.start()-20)
    print(f'Array {i}: pos={m.start()}, len={len(m.group())}')
    print(m.group()[:200])
    print('---')
    if i > 3: break

# Find the e() or a() function definition (deobfuscation function)
print('\n--- Deobfuscation function ---')
for m in re.finditer(r'function\s+(\$0|_0x[0-9a-f]+)\s*\([^)]*\)\s*\{[^}]{0,300}\}', js):
    print(m.group()[:300])
    print('---')

# Look specifically around window[...+"pt"] pattern (encrypt/decrypt function)
print('\n--- window[...encrypt/decrypt] functions ---')
for m in re.finditer(r'window\[[^\]]{0,50}["\+]["\]].{0,600}', js):
    ctx = m.group()
    if 'AES' in ctx or 'CryptoJS' in ctx or 'ch7CR' in ctx or 'parse' in ctx:
        print(ctx[:600])
        print('=====')
