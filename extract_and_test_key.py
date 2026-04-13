"""Extract ALL string table entries (both quote styles) and find key."""
import requests, re, base64, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# x1 function is at pos=25875, length 1454
func_start = 25875
func_body_end = func_start + 1454
func_body = js[func_start:func_body_end+10]

# Find the array start  
arr_start_offset = func_body.index('[')
arr_raw = func_body[arr_start_offset:]
# Find matching ]
depth = 0
for i, ch in enumerate(arr_raw):
    if ch == '[': depth += 1
    elif ch == ']':
        depth -= 1
        if depth == 0:
            arr_raw = arr_raw[:i+1]
            break

print(f'Array raw ({len(arr_raw)} chars): {arr_raw[:300]}')
print(f'...end: {arr_raw[-200:]}')

# Extract ALL entries (both quotes)
# Match: "..." and '...'
entries = []
i = 1  # skip opening [
while i < len(arr_raw) - 1:
    if arr_raw[i] in ('"', "'"):
        q = arr_raw[i]
        j = i + 1
        val = []
        while j < len(arr_raw):
            if arr_raw[j] == '\\':
                j += 2
                continue
            if arr_raw[j] == q:
                break
            val.append(arr_raw[j])
            j += 1
        entries.append(''.join(val))
        i = j + 1
    else:
        i += 1

print(f'\nTotal entries: {len(entries)}')
print(f'All entries:')
for idx, e in enumerate(entries):
    print(f'  [{idx}] {e!r}')

# Verify ch7CR is there
cidx = None
for i, e in enumerate(entries):
    if e == 'ch7CR':
        cidx = i
        break
print(f'\nch7CR at index: {cidx}')

# a0(n) = x1()[n-130]
# e(169) = x1()[169-130] = x1()[39] = "ch7CR"
# So shuffled[39] = "ch7CR"
# ch7CR is at original position cidx
# After rotation k: shuffled[i] = original[(i+k)%n]
# shuffled[39] = original[(39+k)%n] = "ch7CR" at original cidx
# (39+k)%n = cidx => k = (cidx - 39) % n

n = len(entries)
if cidx is not None:
    k = (cidx - 39) % n
    print(f'Rotation k = {k}')
    
    def shuffled_get(idx):
        return entries[(idx + k) % n]
    
    print(f'e(169) = x1()[39] = {shuffled_get(39)!r} (should be "ch7CR")')
    e149 = shuffled_get(19)
    e224 = shuffled_get(94)
    print(f'e(149) = x1()[19] = {e149!r}')
    print(f'e(224) = x1()[94] = {e224!r}')
    
    key_str = e149 + "ch7CR" + e224 + "Q"
    print(f'\nKey string: {key_str!r} ({len(key_str)} chars)')
    
    # Fetch CT
    r0 = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
    d = r0.json()
    content = d['data']['content']
    outer = base64.b64decode(content + '==')
    sep = b'","value":"'
    p2 = outer.find(sep); vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv16 = outer[7:23]
    ct = base64.b64decode(outer[vs:ct_end] + b'==')
    print(f'CT: {len(ct)}B, IV: {iv16.hex()}')
    
    # Test: CryptoJS.enc.Utf8.parse(key_str) truncates to 32B for AES-256
    # or uses raw UTF8 bytes - the key length matters
    key_bytes = key_str.encode('utf-8')
    print(f'Key bytes: {key_bytes.hex()} (len={len(key_bytes)})')
    
    def try_decrypt(kb, iv, label=''):
        """Try AES-CBC decrypt with standard key sizes."""
        # Try key as-is (if valid AES size) and padded/truncated to 16/24/32
        sizes = [(s,) for s in [16,24,32] if s == len(kb)] + [(16,), (24,), (32,)]
        for (sz,) in sizes[:4]:
            try:
                if len(kb) >= sz:
                    k2 = kb[:sz]
                else:
                    k2 = (kb * ((sz//len(kb))+2))[:sz]
                ecb = AES.new(k2, AES.MODE_ECB)
                lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
                pv = lp[-1]
                if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): continue
                pt = unpad(AES.new(k2, AES.MODE_CBC, iv).decrypt(ct), 16)
                text = pt.decode('utf-8')
                viet = ['chuong','khong','nguoi','trong','duoc','la ','va ','cua ']
                score = sum(text.lower().encode('ascii','ignore').decode().count(w) for w in viet)
                print(f'  DECRYPTED ({label}, {sz}B key) score={score}: {repr(text[:100])}')
                if score >= 3: return k2
            except Exception as e:
                pass
        return None
    
    # Test with dynamic IV from content (mobile format)
    print('\n--- Test with dynamic IV from content ---')
    r = try_decrypt(key_bytes, iv16, 'dynamic_iv')
    if r: print(f'*** KEY FOUND: {r.hex()} ***')
    
    # Test with IV = UTF8 parse of key (web format)
    print('\n--- Test with IV = Utf8.parse(key_str) ---')
    # CryptoJS Utf8.parse gives raw UTF8 bytes, take first 16 for IV
    key_as_iv = key_bytes[:16] if len(key_bytes) >= 16 else (key_bytes*3)[:16]
    r2 = try_decrypt(key_bytes, key_as_iv, 'static_key_iv')
    if r2: print(f'*** KEY FOUND (web): {r2.hex()} ***')
    
    # Also try all rotations
    print('\n--- Testing all possible rotation values ---')
    for kk in range(n):
        e149t = entries[(19 + kk) % n]
        e224t = entries[(94 + kk) % n]
        key_test = e149t + "ch7CR" + e224t + "Q"
        if key_test == key_str: continue
        kb = key_test.encode('utf-8')
        result = try_decrypt(kb, iv16, f'rot{kk}:{key_test!r}')
        if result: 
            print(f'*** KEY FOUND at rot={kk}: {result.hex()} ***')
            break
else:
    print('ERROR: ch7CR not found in entries!')
    # Try brute force all entries as key parts
    print('Trying all combinations...')
