"""Extract full string array from obfuscated JS and simulate rotation to find AES key."""
import requests, re, base64, ast, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Fetch chapter CT
def get_ct():
    r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
    d = r.json()
    content = d['data']['content']
    outer = base64.b64decode(content + '==')
    sep = b'","value":"'
    pos = outer.find(sep); vs = pos + len(sep)
    ct_end = outer.find(b'"', vs)
    iv16 = outer[7:23]
    ct = base64.b64decode(outer[vs:ct_end] + b'==')
    return iv16, ct

iv16, ct = get_ct()
print(f'CT: {len(ct)}B, IV: {iv16.hex()}')

def check_strict(key_bytes, label=''):
    try:
        if len(key_bytes) not in (16,24,32): return False
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        lp = bytes(a^b for a,b in zip(ecb.decrypt(ct[-16:]), ct[-32:-16]))
        pv = lp[-1]
        if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): return False
        pt = unpad(AES.new(key_bytes, AES.MODE_CBC, iv16).decrypt(ct), 16)
        t = pt.decode('utf-8')
        viet = ['chuong','khong','nguoi','trong','duoc','la ','va ','cua ']
        score = sum(t.lower().encode('ascii','ignore').decode().count(w) for w in viet)
        print(f'  PASS ({label}) score={score}: {repr(t[:80])}')
        return score >= 3
    except: return False

# Load JS
with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Find function x1() definition - it returns the string array
# Pattern: function x1(){return _0x..._}
print('\n--- Looking for x1 function ---')
x1_matches = re.findall(r'function x1\(\)\{return ([^}]+)\}', js)
for m in x1_matches[:3]:
    print(f'x1 returns: {m[:100]}')

# Look for const/var assignment ending in the array
# common pattern: var _0xXXXX = ["a","b",...]; function x1(){return _0xXXXX;}
print('\n--- Looking for array variable assignment ---')
arr_matches = re.findall(r'((?:var|const|let)\s+(_0x[0-9a-fA-F]+)\s*=\s*\[([^\]]{500,})\])', js)
for am in arr_matches[:3]:
    varname, varname2, content = am
    entries = re.findall(r'"([^"]*)"', content)
    print(f'Array variable: {varname2}, {len(entries)} entries')
    print(f'  First 20: {entries[:20]}')
    print(f'  Last 10: {entries[-10:]}')

# Alternative: inline array in x1 function
print('\n--- Inline x1 patterns ---')
x1_inline = re.findall(r'function x1\(\)\{(?:return\s*)?\[([^\]]{100,})\]', js)
for m in x1_inline[:2]:
    entries = re.findall(r'"([^"]*)"', m)
    print(f'Found {len(entries)} entries inline')
    if entries:
        print(f'  First: {entries[:10]}')
        print(f'  Last: {entries[-10:]}')

# Search for the specific sequence around ch7CR in the array
print('\n--- Finding ch7CR in full array context ---')
# The string table is usually a long array at start of file
# Look for it by finding a large contiguous run of quoted strings
big_str_arrays = re.finditer(r'(?:var|const|let)\s+(?P<name>_0x[0-9a-f]{4,})\s*=\s*\[(?P<arr>"(?:[^"]*)",?){40,}\]', js)
for m in big_str_arrays:
    name = m.group('name')
    arr_content = js[m.start():m.end()]
    entries = re.findall(r'"([^"]*)"', arr_content)
    print(f'Found array {name}: {len(entries)} entries')
    if 'ch7CR' in entries:
        idx = entries.index('ch7CR')
        print(f'  ch7CR at index {idx}')
        print(f'  Entries around it: {entries[max(0,idx-5):idx+6]}')
    break

# Try yet another approach - look at the actual rotation target
# function x1 is defined somewhere
print('\n=== FULL x1 search ===')
for m in re.finditer(r'x1[^;]{0,500}', js):
    ctx = m.group()
    if 'return' in ctx and '[' in ctx:
        print(ctx[:300])
        print('---')
        break
