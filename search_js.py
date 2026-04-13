"""
Download the metruyencv.com web JS bundle and search for:
1. AES/CryptoJS decrypt patterns
2. APP_KEY or cipher key strings
3. Any decryption logic involving chapter content
"""
import sys, re, requests, base64, hmac, hashlib
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JS_URL = 'https://metruyencv.com/build/assets/app-ed2d0a7f.js'
CACHE_PATH = r'C:\Dev\MTC_Download\app-ed2d0a7f.js'
import os
if os.path.exists(CACHE_PATH):
    print(f'Using cached JS bundle: {CACHE_PATH}')
    with open(CACHE_PATH, 'r', encoding='utf-8', errors='replace') as f:
        js = f.read()
else:
    print(f'Downloading {JS_URL}...')
    r = requests.get(JS_URL, timeout=60, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'  Status: {r.status_code}, size: {len(r.content):,} bytes')
    js = r.text
    with open(CACHE_PATH, 'w', encoding='utf-8', errors='replace') as f:
        f.write(js)

print(f'JS bundle size: {len(js):,} chars')

# ============================================================
# 1. Search for AES / CryptoJS patterns
# ============================================================
print('\n=== Searching for AES/Crypto patterns ===')
crypto_patterns = [
    r'CryptoJS',
    r'AES\.decrypt',
    r'AES\.encrypt',
    r'\.decrypt\(',
    r'\.encrypt\(',
    r'createDecipheriv',
    r'createCipheriv',
    r'crypto\.subtle',
    r'importKey',
    r'decryptContent',
    r'decryptChapter',
]
for p in crypto_patterns:
    matches = list(re.finditer(p, js))
    if matches:
        print(f'  {p}: {len(matches)} matches')
        for m in matches[:2]:
            start = max(0, m.start()-80)
            end = min(len(js), m.end()+100)
            snippet = js[start:end].replace('\n','↵')
            print(f'    ...{snippet}...')

# ============================================================
# 2. Search for key-like strings
# ============================================================
print('\n=== Searching for key-like strings ===')
# Laravel APP_KEY pattern: base64:XXXXX or 32-char printable strings
key_patterns = [
    r'base64:[A-Za-z0-9+/]{40,}={0,2}',
    r'"[A-Za-z0-9+/]{40,}={0,2}"',  # long base64 values in quotes
    r"'[A-Za-z0-9+/]{40,}={0,2}'",
    r'APP_KEY',
    r'cipher.*key',
    r'secret.*key',
    r'decrypt.*key',
]
for p in key_patterns:
    matches = list(re.finditer(p, js, re.IGNORECASE))
    if matches:
        print(f'  Pattern {p!r}: {len(matches)} matches')
        for m in matches[:3]:
            start = max(0, m.start()-40)
            end = min(len(js), m.end()+40)
            snippet = js[start:end].replace('\n','↵')
            print(f'    {snippet}')

# ============================================================
# 3. Search for content decryption function
# ============================================================
print('\n=== Searching for content handling ===')
content_patterns = [
    r'content',
    r'chapter',
    r'iv',
    r'mac',
]
# Find where content/chapter field is used in decrypt context
for p in [r'content.*decrypt', r'decrypt.*content', r'\.content.*\biv\b', r'"iv".*"mac"']:
    matches = list(re.finditer(p, js, re.IGNORECASE))
    if matches:
        print(f'  {p}: {len(matches)} matches')
        for m in matches[:2]:
            start = max(0, m.start()-60)
            end = min(len(js), m.end()+120)
            snippet = js[start:end].replace('\n','↵')
            print(f'    {snippet}')

# ============================================================
# 4. Find all 16-32 char printable ASCII strings
# ============================================================
print('\n=== 16-32 char key-like printable strings (quoted) ===')
key16 = re.findall(r'["\']([A-Za-z0-9+/=_\-!@#$%^&*]{16,32})["\']', js)
# Deduplicate and show unique
unique_keys = sorted(set(key16))
print(f'  Found {len(unique_keys)} unique 16-32 char quoted strings')
# Filter: likely key candidates (mixed case + digits, not common words)
candidates = [k for k in unique_keys
              if (any(c.isdigit() for c in k) and
                  any(c.islower() for c in k) and
                  any(c.isupper() for c in k))]
print(f'  Of which {len(candidates)} have mixed case+digits (key-like):')
for k in candidates[:30]:
    print(f'    {k!r}')

# ============================================================
# 5. Test all key candidates against MAC oracle
# ============================================================
print('\n=== Testing candidates against MAC oracle ===')
import requests as req2
r5 = req2.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
d5 = r5.json()
chap = d5['data']
content_str = chap['content']
pad = '=' * (-len(content_str) % 4)
outer = base64.b64decode(content_str + pad)
sep = b'","value":"'
p2 = outer.find(sep); vs = p2 + len(sep)
ct_end = outer.find(b'"', vs)
iv_raw = outer[7:p2]
val_b64 = outer[vs:ct_end]
mac_s = outer.find(b'"mac":"'); mac_e = outer.find(b'"', mac_s+7)
mac_hex = outer[mac_s+7:mac_e].decode('ascii')
print(f'MAC target: {mac_hex[:20]}...')

for k_str in candidates:
    k = k_str.encode('utf-8')
    h = hmac.new(k, iv_raw + val_b64, hashlib.sha256).hexdigest()
    if h == mac_hex:
        print(f'  *** MAC MATCH: {k_str!r}')
    # Also try b64-decoded version if it could be a base64 key
    if len(k_str) in (24, 44) and k_str.endswith('='):
        try:
            k_dec = base64.b64decode(k_str)
            h2 = hmac.new(k_dec, iv_raw + val_b64, hashlib.sha256).hexdigest()
            if h2 == mac_hex:
                print(f'  *** MAC MATCH (b64-decoded): {k_str!r} -> {k_dec.hex()}')
        except: pass

print('\nDone.')
