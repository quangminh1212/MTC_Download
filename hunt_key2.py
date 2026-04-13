"""
1. Extract all interesting strings from libapp.so 
2. Try derived keys: SHA256/MD5 of common seeds
3. Probe API endpoints other than chapters
"""
import re, base64, hashlib, requests, json

# --- Fetch cipher data ---
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content = r.json()['data']['content']
outer = base64.b64decode(content + '==')
sep = b'","value":"'
pos = outer.find(sep); vs = pos + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

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

# --- Extract strings from libapp.so ---
data = open(r'C:\Dev\MTC_Download\libapp_extracted\libapp.so', 'rb').read()
# Null-terminated ASCII strings length 8-64
STR_RE = re.compile(rb'[ -~]{8,64}\x00')
strings = set(m.group()[:-1].decode('ascii') for m in STR_RE.finditer(data))
print(f'Total printable strings (8-64 chars, null-terminated): {len(strings)}')

# Look for key-like strings: no spaces, mixed case/digits, 16-44 chars
key_like = [s for s in strings if
    8 <= len(s) <= 44 and
    ' ' not in s and
    not s.startswith('http') and
    not s.startswith('com.') and
    not s.startswith('android') and
    not all(c.isalpha() for c in s)]  # not pure alpha

print(f'Key-like strings: {len(key_like)}')
# Print first 100
for s in sorted(key_like)[:100]:
    print(f'  {len(s):2d}: {s!r}')

print()
# --- Try derived keys ---
print('=== Derived key attempts ===')
seeds = [
    b'lonoapp', b'novelfever', b'novelfeverx', b'novelfeverapp',
    b'android.lonoapp.net', b'lonoapp.net', b'mtruyen', b'MTC',
    b'truyen.onl', b'flutter_app', b'aes_key', b'secret_key',
    b'@lonoapp', b'lonoapp@secret', b'NovelfeverX',
    # From strings found above (will add after seeing them)
]
derived_tested = 0
for seed in seeds:
    for h, func in [('md5',  lambda s: hashlib.md5(s).digest()),
                    ('sha1', lambda s: hashlib.sha1(s).digest()[:16]),
                    ('sha256-16', lambda s: hashlib.sha256(s).digest()[:16]),
                    ('sha256-32', lambda s: hashlib.sha256(s).digest()),
                    ('sha512-16', lambda s: hashlib.sha512(s).digest()[:16]),
                    ('sha512-32', lambda s: hashlib.sha512(s).digest()[:32])]:
        key = func(seed)
        if check_strict(key):
            print(f'FOUND: {h}({seed!r}) = {key.hex()}')
            derived_tested += 1
            break
        derived_tested += 1

print(f'Derived keys tested: {derived_tested}')

# --- Probe API endpoints ---
print('\n=== API endpoint probing ===')
base_urls = ['https://android.lonoapp.net/api', 'https://api.lonoapp.net/api']
endpoints = ['/config', '/settings', '/app/config', '/app/setting', 
             '/app', '/init', '/version', '/key', '/public-key']
for base in base_urls:
    for ep in endpoints:
        try:
            rr = requests.get(base+ep, timeout=5, 
                             headers={'User-Agent': 'okhttp/4.9.1'})
            if rr.status_code != 404:
                print(f'  {base+ep}: HTTP {rr.status_code} -> {rr.text[:200]}')
        except Exception as e:
            pass
print('Done')
