"""
Compute the exact x1 rotation using the real hash formula from JS.
Hash: -parseInt(e(247))/1 * (-parseInt(e(248))/2)
     + -parseInt(e(172))/3 + parseInt(e(152))/4 
     + parseInt(e(234))/5 * (parseInt(e(291))/6)
     + -parseInt(e(223))/7
     + parseInt(e(276))/8 * (-parseInt(e(190))/9)
     + -parseInt(e(181))/10 * (-parseInt(e(277))/11)
     === 650736
where e(n) = a0(n) = x1()[n-130]
"""
import sys, re, base64, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Extract x1 entries (171 entries, already confirmed)
x1_start = 25875
ctx = js[x1_start:x1_start+5000]
arr_rel = ctx.index('[')

def find_array_end(text, start):
    depth = 0; i = start; in_str = None
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == '\\': i += 2; continue
            if ch == in_str: in_str = None
        elif ch in ('"', "'"): in_str = ch
        elif ch == '[': depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0: return i
        i += 1
    return -1

arr_end = find_array_end(ctx, arr_rel)
arr_text = ctx[arr_rel:arr_end+1]

def extract_js_strings(arr_text):
    entries = []; i = 1
    while i < len(arr_text)-1:
        ch = arr_text[i]
        if ch in ('"', "'"):
            q = ch; j = i+1; val = []
            while j < len(arr_text):
                c2 = arr_text[j]
                if c2 == '\\' and j+1 < len(arr_text):
                    val.append({'n':'\n','t':'\t','r':'\r','\\':'\\','"':'"',"'":"'"}.get(arr_text[j+1], arr_text[j+1])); j += 2; continue
                if c2 == q: break
                val.append(c2); j += 1
            entries.append(''.join(val)); i = j+1
        else: i += 1
    return entries

entries = extract_js_strings(arr_text)
n = len(entries)
print(f'x1 entries: {n}')

def js_parseInt(s):
    """JS parseInt(s): parse leading digits (and optional leading minus)."""
    s = s.strip()
    if not s: return float('nan')
    # JS parseInt searches for leading sign + digits
    m = re.match(r'[+-]?\d+', s)
    if m: return int(m.group())
    return float('nan')

def hash_at_rotation(k):
    """Compute hash expression after k left-rotations."""
    # x1()[i] after k rotations = entries[(i+k) % n]
    def x1i(i): return entries[(i + k) % n]
    # e(n) = a0(n) = x1()[n-130]
    def e(v): return x1i(v - 130)
    
    h = ((-js_parseInt(e(247))/1) * (-js_parseInt(e(248))/2)
         + (-js_parseInt(e(172))/3)
         + (js_parseInt(e(152))/4)
         + (js_parseInt(e(234))/5) * (js_parseInt(e(291))/6)
         + (-js_parseInt(e(223))/7)
         + (js_parseInt(e(276))/8) * (-js_parseInt(e(190))/9)
         + (-js_parseInt(e(181))/10) * (-js_parseInt(e(277))/11))
    return h

print('\nFinding rotation k where hash == 650736 ...')
target = 650736
for k in range(n):
    h = hash_at_rotation(k)
    if abs(h - target) < 0.001:
        print(f'Found! k={k}, hash={h}')
        break
    if k < 5 or k % 20 == 0:
        print(f'  k={k}: hash={h:.4f}')
else:
    print(f'Not found in {n} rotations!')
    print('Showing all hashes:')
    for k in range(n):
        h = hash_at_rotation(k)
        print(f'  k={k}: hash={h:.6f}  (entries sample: {entries[k]!r})')
    sys.exit(1)

# Once k found, get key fragments
def x1i(i): return entries[(i + k) % n]
def a0(v): return x1i(v - 130)

print(f'\nWith k={k}:')
print(f'a0(169) = x1()[39] = {a0(169)!r}  (should be ch7CR)')
print(f'a0(149) = x1()[19] = {a0(149)!r}')
print(f'a0(224) = x1()[94] = {a0(224)!r}')
key_str = a0(149) + "ch7CR" + a0(224) + "Q"
print(f'Key: {key_str!r}  ({len(key_str)} chars)')

# Now test decryption
print('\n--- Fetching chapter 21589884 ---')
r0 = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
d = r0.json()
content_raw = d['data']['content']
outer = base64.b64decode(content_raw + '==')
sep = b'","value":"'
p2 = outer.find(sep); vs = p2 + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')
print(f'outer (16B): {outer[:16].hex()}  {outer[:16]!r}')
print(f'IV (7:23): {iv16.hex()}  {iv16!r}')
print(f'CT: {len(ct)}B')

key_bytes = key_str.encode('utf-8')
print(f'Key bytes: {key_bytes.hex()}  (len={len(key_bytes)})')

def try_key(tag, kb, iv):
    for sz in [16, 24, 32]:
        kb2 = kb[:sz] if len(kb)>=sz else (kb*(sz//len(kb)+2))[:sz]
        try:
            ecb = AES.new(kb2, AES.MODE_ECB)
            lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
            pv = lp[-1]
            if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): continue
            pt = unpad(AES.new(kb2, AES.MODE_CBC, iv).decrypt(ct), 16)
            text = pt.decode('utf-8')
            viet = ['chương','không','người','trong','được']
            sc = sum(text.lower().count(w) for w in viet)
            print(f'  VALID! {tag} sz={sz} score={sc}: {text[:100]!r}')
            return kb2
        except: pass
    return None

results = []
for tag, iv in [
    ('mobile_iv', iv16),
    ('key_as_iv', key_bytes[:16] if len(key_bytes)>=16 else (key_bytes*2)[:16]),
    ('zero_iv', b'\x00'*16),
]:
    r = try_key(tag, key_bytes, iv)
    if r: results.append((tag, r))

if results:
    for tag, r in results:
        print(f'\n*** KEY FOUND ({tag}): {r.hex()} ***')
else:
    print('\nDecryption failed with all IVs. Inspecting content format...')
    print(f'outer full (first 200): {outer[:200]!r}')
    # Maybe structure is different
    # Try: outer is a JSON string, iv field is base64-encoded
    text = outer.decode('utf-8', errors='replace')
    print(f'As text: {text[:200]}')
