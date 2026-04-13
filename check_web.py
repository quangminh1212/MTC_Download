"""Check metruyencv.com for AES key in JavaScript and API."""
import requests, re, base64, hashlib

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

# Fetch metruyencv.com
r = requests.get('https://metruyencv.com', timeout=15, headers=HEADERS)
print(f'metruyencv.com: HTTP {r.status_code}')
title_m = re.search(r'<title[^>]*>(.*?)</title>', r.text, re.DOTALL)
print(f'Title: {title_m.group(1)[:80] if title_m else "not found"}')

# Find JS bundle files
js_files = re.findall(r'src=["\']([^"\']+\.js)', r.text)
print(f'JS files found: {len(js_files)}')
for j in js_files[:10]:
    print(f'  {j}')

# Try chapter API on web
print('\n--- Trying chapter API on metruyencv.com ---')
for url in [
    'https://metruyencv.com/api/chapters/21589884',
    'https://api.metruyencv.com/api/chapters/21589884',
    'https://metruyencv.com/chuong/21589884',
]:
    try:
        rr = requests.get(url, timeout=8, headers=HEADERS)
        print(f'{url}: HTTP {rr.status_code}')
        if rr.status_code == 200:
            print(f'  Content: {rr.text[:200]}')
    except Exception as e:
        print(f'{url}: {e}')

# Try to find key in web JS
print('\n--- Scanning JS files for key material ---')
for j in js_files[:30]:
    if not j.startswith('http'):
        j = 'https://metruyencv.com' + j
    try:
        js = requests.get(j, timeout=10, headers=HEADERS)
        if js.status_code != 200: continue
        js_text = js.text
        # Look for AES-related patterns
        found_aes = any(pat in js_text for pat in ['AES', 'aes', 'encrypt', 'decrypt', 'cipher'])
        if found_aes:
            print(f'  {j}: AES patterns found! ({len(js_text)} bytes)')
            # Look for key-like strings
            key_pats = re.findall(r'["\'][A-Za-z0-9+/\-_]{24,44}={0,2}["\']', js_text)
            for kp in key_pats[:20]:
                kp_clean = kp.strip("\"'")
                for pad in ['', '=', '==']:
                    try:
                        k = base64.b64decode(kp_clean + pad)
                        if len(k) in (16,24,32):
                            ok = check_strict(k)
                            print(f'    b64 candidate: {kp_clean!r} -> {k.hex()} -> {"FOUND!" if ok else "no"}')
                            if ok: 
                                print(f"*** KEY FOUND: {k.hex()} ***")
                    except: pass
        # Look for crypto-js patterns
        if 'CryptoJS' in js_text:
            print(f'  {j}: CryptoJS found!')
    except Exception as e:
        print(f'  {j}: error {e}')

# Also try pub.truyen.onl
print('\n--- pub.truyen.onl ---')
r2 = requests.get('https://pub.truyen.onl/', timeout=10, headers=HEADERS)
print(f'HTTP {r2.status_code}: {r2.text[:200]}')
