"""Scan libflutter.so and libapp.so.bak for base64/hex encoded keys."""
import time, base64, re, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content = r.json()['data']['content']
outer = base64.b64decode(content + '==')
sep = b'","value":"'
pos = outer.find(sep); vs = pos + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')
print(f'ct: {len(ct)}B, ct%16={len(ct)%16}')

def check_key(key_bytes):
    try:
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
        pv = lp[-1]
        if not (1 <= pv <= 16): return False
        if any(lp[-pv+i] != pv for i in range(pv)): return False
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv16)
        pt = unpad(cipher.decrypt(ct), 16)
        s = pt.decode('utf-8', errors='replace')
        return sum(1 for c in s if '\u00C0' <= c <= '\u1EFF') >= 10
    except: return False

B64_RE = re.compile(rb'[A-Za-z0-9+/\-_]{22,48}={0,2}')
HEX_RE = re.compile(rb'[0-9a-fA-F]{32,64}')

libs = [
    ('libflutter.so', r'C:\Dev\MTC_Download\libflutter_extracted\libflutter.so'),
    ('libapp.bak',    r'C:\Dev\MTC_Download\libflutter_extracted\libapp.so.bak'),
]

for libname, libpath in libs:
    t0 = time.time()
    data = open(libpath, 'rb').read()
    keys = set()
    for m in B64_RE.finditer(data):
        s = m.group()
        for v in [s, s.replace(b'-', b'+').replace(b'_', b'/')]:
            for p in [b'', b'=', b'==']:
                try:
                    d = base64.b64decode(v+p)
                    if len(d) in (16, 24, 32): keys.add(d)
                except: pass
    for m in HEX_RE.finditer(data):
        s = m.group().decode()
        for n in (32, 48, 64):
            if len(s) >= n:
                try:
                    d = bytes.fromhex(s[:n])
                    if len(d) in (16, 24, 32): keys.add(d)
                except: pass
    found = next((k for k in keys if check_key(k)), None)
    label = f"FOUND: {found.hex()}" if found else "NOT FOUND"
    print(f'{libname}: {len(keys)} candidates -> {label}  ({time.time()-t0:.1f}s)')
