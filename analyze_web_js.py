"""Test candidates from web JS and extract more context."""
import requests, re, base64, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Fix encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Fetch chapter CT
r0 = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content = r0.json()['data']['content']
outer = base64.b64decode(content + '==')
sep = b'","value":"'
pos = outer.find(sep); vs = pos + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')

def check_strict(key_bytes, label=''):
    try:
        if len(key_bytes) not in (16,24,32): return False
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
        pv = lp[-1]
        if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): return False
        pt = unpad(AES.new(key_bytes, AES.MODE_CBC, iv16).decrypt(ct), 16)
        t = pt.decode('utf-8')
        viet = ['chuong','khong','nguoi','trong','duoc','la ','va ','cua ','co ']
        score = sum(t.lower().count(w) for w in viet)
        print(f'  DECRYPTED ({label}): score={score}, preview={t[:100]}')
        return score >= 3
    except Exception as e: 
        return False

# Test the hardcoded IV array as KEY
iv_chars = [84,103,66,57,120,87,109,75,113,89,55,49,82,100,78,99]
key_str = ''.join(chr(c) for c in iv_chars)
print(f'Hardcoded array string: {key_str!r}')
k = key_str.encode()
print(f'As UTF-8 key ({len(k)}B): {k.hex()}')
ok = check_strict(k, label='hardcoded_iv_array')
if ok: print(f'*** FOUND: {k.hex()} ***')

# Download JS and analyze
print('\nDownloading JS...')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}
r = requests.get('https://metruyencv.com/build/assets/app-ed2d0a7f.js', timeout=30, headers=HEADERS)
js = r.text
print(f'JS size: {len(js)} chars')

# Save to disk for analysis
with open('app_bundle.js', 'w', encoding='utf-8') as f:
    f.write(js)
print('Saved to app_bundle.js')

# Find the "ch7CR" pattern and surrounding context
print('\n--- ch7CR pattern ---')
for m in re.finditer(r'.{0,200}ch7CR.{0,200}', js):
    print(m.group())
    print('---')

# Look at 'e(149)' pattern context (key building)
print('\n--- Key building pattern with e(149) ---')
for m in re.finditer(r'n\s*=\s*t\s*\?\?[^;]{0,200}', js):
    print(m.group()[:300])
    print('---')

# Find ALL obfuscated string arrays _0x in JS
print('\n--- String array candidates ---')
arrays = re.findall(r'\[(?:"[^"]*",\s*){10,}', js)
print(f'Found {len(arrays)} string arrays')
for a in arrays[:2]:
    print(a[:200])
    print('---')

# Look for AES key near decrypt function
print('\n--- decrypt function context ---')
for m in re.finditer(r'(?:decrypt|Decrypt)[^}]{0,500}', js):
    ctx = m.group()
    if 'key' in ctx.lower() or 'CBC' in ctx:
        print(ctx[:400])
        print('---')

# Look for the specific hardcoded IV context
print('\n--- Context around hardcoded [84,103 array ---')
for m in re.finditer(r'.{0,300}\[84,103,.{0,300}', js):
    ctx = m.group()
    print(ctx[:600])
    print('---')
