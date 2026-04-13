"""
1. Simulate the REAL JS rotation (hash-based) to get definitive x1 indices
2. Inspect actual outer content format
3. Test decryption with all reasonable IV variants
"""
import re, base64, sys, ctypes, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# ---- Step 1: Extract the full x1 array (already confirmed 171 entries) ----
x1_start = 25875
ctx = js[x1_start:x1_start+5000]
arr_rel = ctx.index('[')

def find_array_end(text, start):
    depth = 0
    i = start
    in_str = None
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == '\\': i += 2; continue
            if ch == in_str: in_str = None
        elif ch in ('"', "'"):
            in_str = ch
        elif ch == '[': depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1

arr_end = find_array_end(ctx, arr_rel)
arr_text = ctx[arr_rel:arr_end+1]

def extract_js_strings(arr_text):
    entries = []
    i = 1
    while i < len(arr_text) - 1:
        ch = arr_text[i]
        if ch in ('"', "'"):
            q = ch; j = i+1; val = []
            while j < len(arr_text):
                c2 = arr_text[j]
                if c2 == '\\' and j+1 < len(arr_text):
                    val.append({'n':'\n','t':'\t','r':'\r','\\':'\\','"':'"',"'":"'"}.get(arr_text[j+1], arr_text[j+1]))
                    j += 2; continue
                if c2 == q: break
                val.append(c2); j += 1
            entries.append(''.join(val)); i = j+1
        else: i += 1
    return entries

entries = extract_js_strings(arr_text)
print(f'x1 entries: {len(entries)}')

# ---- Step 2: Find the rotation target from JS ----
# Pattern: (function(x,t){...x().push(x().shift())...})(x1, NNNNN)
rot_m = re.search(r'\}\)\(x1,\s*(\d+)\)', js)
target_str = rot_m.group(1) if rot_m else None
print(f'Rotation target (string): {target_str}')

# Also check for signed negative targets
rot_m2 = re.search(r'\}\)\(x1,\s*(-?\d+)\)', js)
target = int(rot_m2.group(1)) if rot_m2 else None
print(f'Rotation target: {target}')

# ---- Step 3: JS djb2 hash (matching JS `c<<5)-c+charCode|0`) ----
def js_hash(s):
    """Emulate JS: c=(c<<5)-c+n.charCodeAt(i)|0"""
    c = 0
    for ch in s:
        c = ctypes.c_int32((c << 5) - c + ord(ch)).value
    return c

# ---- Step 4: Simulate rotation ----
arr = list(entries)  # copy
n = len(arr)
print(f'\nSimulating rotation toward target={target}...')
print(f'Initial arr[0]={arr[0]!r}, hash={js_hash(arr[0])}')

k = 0
max_iter = n * 2  # safety limit
while k < max_iter:
    h = js_hash(arr[0])
    if h == target:
        print(f'Rotation done! k={k}, arr[0]={arr[0]!r}, hash={h}')
        break
    arr.append(arr.pop(0))  # left rotate (push(shift()))
    k += 1
else:
    print(f'Target {target} not reached! Trying all {n} positions...')
    arr = list(entries)
    for kk in range(n):
        if js_hash(arr[0]) == target:
            k = kk
            print(f'Found at k={kk}!')
            break
        arr.append(arr.pop(0))
    else:
        print(f'ERROR: hash target never matched!')
        # Show hashes for all positions
        arr = list(entries)
        for kk in range(n):
            print(f'  k={kk}: arr[0]={arr[0]!r} hash={js_hash(arr[0])}')
            arr.append(arr.pop(0))
        sys.exit(1)

# arr is now the ROTATED (shuffled) array
print(f'\nx1()[19]  = arr[19]  = {arr[19]!r}')
print(f'x1()[39]  = arr[39]  = {arr[39]!r}  (should be ch7CR)')
print(f'x1()[94]  = arr[94]  = {arr[94]!r}')

e149 = arr[19]; e169 = arr[39]; e224 = arr[94]
key_str = e149 + "ch7CR" + e224 + "Q"
key_str2 = e149 + e169 + e224 + "Q"
print(f'\nKey v1 (literal ch7CR): {key_str!r}  ({len(key_str)}B)')
print(f'Key v2 (e169={e169!r}): {key_str2!r}  ({len(key_str2)}B)')

# ---- Step 5: Fetch chapter and inspect raw content ----
print('\n--- Fetching chapter 21589884 ---')
r0 = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
d = r0.json()
content_raw = d['data']['content']
print(f'content_raw (first 200): {content_raw[:200]!r}')
print(f'content_raw type/len: {type(content_raw).__name__}, {len(content_raw)}')

outer = base64.b64decode(content_raw + '==')
print(f'\nouter ({len(outer)} bytes) hex first 80: {outer[:80].hex()}')
print(f'outer as text (first 100): {outer[:100]!r}')

sep = b'","value":"'
p2 = outer.find(sep)
print(f'\nsep found at pos {p2}')
if p2 >= 0:
    vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv16 = outer[7:23]
    ct_b64 = outer[vs:ct_end]
    ct = base64.b64decode(ct_b64 + b'==')
    print(f'iv16 ({len(iv16)}B): {iv16.hex()}  as text: {iv16!r}')
    print(f'ct_b64 ({len(ct_b64)}B): {ct_b64[:60]!r}...')
    print(f'ct ({len(ct)}B)')
    
    # What's in front of the value?
    iv_raw = outer[p2-16:p2]
    print(f'\nouter[{p2-16}:{p2}] = {iv_raw!r}')
    
    for s_offset in range(max(0, p2-30), p2):
        chunk = outer[s_offset:s_offset+16]
        if len(chunk) == 16:
            txt = ''.join(chr(b) if 0x20 <= b < 0x7F else '.' for b in chunk)
            print(f'  [7:{s_offset+16}] {chunk.hex()} = {txt!r}')

# ---- Step 6: Test decryption ----
def try_key(tag, kb, iv_bytes):
    for sz in [16, 24, 32]:
        if len(kb) == sz: kb2 = kb
        elif len(kb) > sz: kb2 = kb[:sz]
        else: kb2 = (kb * (sz//len(kb)+2))[:sz]
        try:
            ecb = AES.new(kb2, AES.MODE_ECB)
            lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
            pv = lp[-1]
            if not (1 <= pv <= 16) or any(lp[-i] != pv for i in range(1, pv+1)):
                continue
            # Valid padding!
            pt = unpad(AES.new(kb2, AES.MODE_CBC, iv_bytes).decrypt(ct), 16)
            text = pt.decode('utf-8')
            viet = ['chương', 'không', 'người', 'trong', 'được']
            sc = sum(text.lower().count(w) for w in viet)
            print(f'  VALID PADDING+DECRYPT! {tag} sz={sz} score={sc}: {text[:120]!r}')
            return kb2
        except Exception as e:
            pass
    return None

kb1 = key_str.encode('utf-8')
kb2 = key_str2.encode('utf-8') if key_str2 != key_str else None

iv_dynamic = iv16
iv_from_key = kb1[:16] if len(kb1)>=16 else (kb1*3)[:16]

print(f'\n--- Decryption tests ---')
for tag, kb, iv in [
    ('v1_dynamic_iv', kb1, iv_dynamic),
    ('v1_key_as_iv', kb1, iv_from_key),
    ('v1_zero_iv', kb1, b'\x00'*16),
]:
    r = try_key(tag, kb, iv)
    if r: print(f'*** KEY FOUND: {r.hex()} ***')

if kb2:
    for tag, iv in [('v2_dynamic', iv_dynamic), ('v2_key_iv', kb2[:16])]:
        r = try_key(tag, kb2, iv)
        if r: print(f'*** KEY FOUND: {r.hex()} ***')
