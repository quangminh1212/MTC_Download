"""
Find:
1. All API URL strings in libapp.so (to find key-fetching endpoints)
2. Content of Flutter translation files (might contain key)
3. Re-run b64/hex scan with STRICT UTF-8 validation on all libs
"""
import base64, re, requests, zipfile, json, time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- Fetch CT ---
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content = r.json()['data']['content']
outer = base64.b64decode(content + '==')
sep = b'","value":"'
pos = outer.find(sep); vs = pos + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')
print(f'ct:{len(ct)}B ct%16={len(ct)%16}\n')

def check_key_strict(key_bytes):
    """Strict: unpad + strict UTF-8 + Vietnamese word check."""
    try:
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
        pv = lp[-1]
        if not (1 <= pv <= 16): return False
        if any(lp[-i] != pv for i in range(1, pv+1)): return False
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv16)
        pt = unpad(cipher.decrypt(ct), 16)
        text = pt.decode('utf-8')  # STRICT - raises on invalid UTF-8
        # Check for actual Vietnamese words
        viet_words = ['chương', 'không', 'người', 'trong', 'được', 'những',
                      'cũng', 'như', 'một', 'đã', 'này', 'của', 'với']
        count = sum(text.lower().count(w) for w in viet_words)
        return count >= 3
    except Exception:
        return False

B64_RE = re.compile(rb'[A-Za-z0-9+/\-_]{22,48}={0,2}')
HEX_RE = re.compile(rb'[0-9a-fA-F]{32,64}')

libs = [
    ('libapp.so',     r'C:\Dev\MTC_Download\libapp_extracted\libapp.so'),
    ('libflutter.so', r'C:\Dev\MTC_Download\libflutter_extracted\libflutter.so'),
    ('libapp.bak',    r'C:\Dev\MTC_Download\libflutter_extracted\libapp.so.bak'),
]

print('=== Strict B64/Hex key scan ===')
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
    found = next((k for k in keys if check_key_strict(k)), None)
    label = f"FOUND: {found.hex()}" if found else f"NOT FOUND ({len(keys)} candidates)"
    print(f'  {libname}: {label}  ({time.time()-t0:.1f}s)')

# --- Scan Flutter assets ---
print('\n=== Flutter assets ===')
z = zipfile.ZipFile(r'C:\Dev\MTC_Download\base.apk')
for name in ['assets/flutter_assets/assets/translations/vi-VN.json',
             'assets/flutter_assets/assets/translations/en-US.json']:
    data = z.open(name).read()
    print(f'\n{name} ({len(data)}B):')
    try:
        j = json.loads(data)
        # Print all string values that look like they could be keys
        def find_strings(obj, path=''):
            if isinstance(obj, str) and 20 <= len(obj) <= 64:
                print(f'  {path}: {obj!r}')
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    find_strings(v, f'{path}.{k}')
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    find_strings(v, f'{path}[{i}]')
        find_strings(j)
    except Exception as e:
        print(f'  (not JSON: {e})')
        print(f'  Raw: {data[:100]}')

# --- Find API URLs in libapp.so ---
print('\n=== API URLs in libapp.so ===')
data = open(r'C:\Dev\MTC_Download\libapp_extracted\libapp.so', 'rb').read()
urls = re.findall(rb'https?://[a-zA-Z0-9./\-_?=&%:]{10,100}', data)
unique_urls = sorted(set(urls))
for u in unique_urls:
    print(f'  {u.decode(errors="replace")}')
