"""Fixed: string-aware bracket tracking to extract full x1 array."""
import re, base64, sys, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# x1 function starts at pos=25875; array ends before pos=27291 (where ];return x1= appears)
# Get a generous slice of the file from x1 start
x1_start = 25875
ctx = js[x1_start:x1_start+2000]

# Find array start
arr_rel = ctx.index('[')
arr_begin = x1_start + arr_rel  # absolute position of '['

# String-aware bracket finder
def find_array_end(text, start):
    """Find the index of the matching ']' for the '[' at text[start]."""
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == '\\':
            i += 2
            continue
        if ch in ('"', "'"):
            q = ch
            i += 1
            while i < len(text):
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1

arr_end_rel = find_array_end(ctx, arr_rel)
if arr_end_rel == -1:
    print('ERROR: could not find array end within 2000 char window, expanding...')
    ctx = js[x1_start:x1_start+5000]
    arr_rel = ctx.index('[')
    arr_end_rel = find_array_end(ctx, arr_rel)

arr_text = ctx[arr_rel:arr_end_rel+1]
print(f'Array: {len(arr_text)} chars (from abs pos {x1_start+arr_rel} to {x1_start+arr_end_rel})')
print(f'Start: {arr_text[:150]}')
print(f'End:   {arr_text[-150:]}')

# Extract all entries (both quote styles, handle escapes)
def extract_js_strings(arr_text):
    entries = []
    i = 1  # skip '['
    while i < len(arr_text) - 1:
        ch = arr_text[i]
        if ch in ('"', "'"):
            q = ch
            j = i + 1
            val = []
            while j < len(arr_text):
                c2 = arr_text[j]
                if c2 == '\\' and j+1 < len(arr_text):
                    nxt = arr_text[j+1]
                    if nxt == 'n': val.append('\n')
                    elif nxt == 't': val.append('\t')
                    elif nxt == 'r': val.append('\r')
                    elif nxt == '\\': val.append('\\')
                    elif nxt == '"': val.append('"')
                    elif nxt == "'": val.append("'")
                    else: val.append('\\'); val.append(nxt)
                    j += 2
                    continue
                if c2 == q:
                    break
                val.append(c2)
                j += 1
            entries.append(''.join(val))
            i = j + 1
        else:
            i += 1
    return entries

entries = extract_js_strings(arr_text)
print(f'\nTotal entries extracted: {len(entries)}')
for idx, e in enumerate(entries):
    print(f'  [{idx:3d}] {e!r}')

# Find ch7CR
cidx = None
for i, e in enumerate(entries):
    if e == 'ch7CR':
        cidx = i
        break

if cidx is None:
    print('\nch7CR NOT in this array!')
    # Check if a different x1 exists elsewhere
    # Search all occurrences of 'function x1(' or 'x1=function('
    for pat in [r'function x1\(', r'var x1\s*=', r'const x1\s*=', r'x1=function\(']:
        for m in re.finditer(pat, js):
            print(f'  x1 pattern {pat!r} at pos {m.start()}: {js[m.start():m.start()+100]}')
else:
    n = len(entries)
    k = (cidx - 39) % n
    print(f'\nch7CR found at index {cidx}, rotation k={k}, n={n}')

    def se(idx):
        return entries[(idx + k) % n]

    print(f'e(169) = x1()[39] = {se(39)!r}  (expect "ch7CR")')
    e149 = se(19)
    e224 = se(94)
    print(f'e(149) = x1()[19] = {e149!r}')
    print(f'e(224) = x1()[94] = {e224!r}')

    key_str = e149 + "ch7CR" + e224 + "Q"
    print(f'\nKey string: {key_str!r}  ({len(key_str)} chars)')

    # Fetch chapter
    r0 = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
    d = r0.json(); content = d['data']['content']
    outer = base64.b64decode(content + '==')
    sep = b'","value":"'; p2 = outer.find(sep); vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv16 = outer[7:23]; ct = base64.b64decode(outer[vs:ct_end] + b'==')
    print(f'CT: {len(ct)}B  IV hex: {iv16.hex()}\n')

    def try_key(tag, kb, iv_bytes):
        for sz in [16,24,32]:
            if len(kb) > sz: kb2 = kb[:sz]
            elif len(kb) == sz: kb2 = kb
            else: kb2 = (kb*(sz//len(kb)+1))[:sz]
            try:
                # Padding check
                ecb = AES.new(kb2, AES.MODE_ECB)
                lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
                pv = lp[-1]
                if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): continue
                pt = unpad(AES.new(kb2, AES.MODE_CBC, iv_bytes).decrypt(ct), 16)
                text = pt.decode('utf-8')
                viet = ['chương','không','người','trong','được']
                sc = sum(text.lower().count(w) for w in viet)
                print(f'  OK {tag} sz={sz}: score={sc} text={text[:80]!r}')
                if sc >= 3: return kb2
            except: pass
        return None

    key_bytes = key_str.encode('utf-8')
    iv_from_content = iv16
    iv_from_key = key_bytes[:16] if len(key_bytes)>=16 else (key_bytes*4)[:16]

    found = try_key('mobile_iv', key_bytes, iv_from_content)
    if found: print(f'*** FOUND: {found.hex()} ***')

    found = try_key('key_as_iv', key_bytes, iv_from_key)
    if found: print(f'*** FOUND: {found.hex()} ***')
