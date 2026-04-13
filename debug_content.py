"""
1. Check if ch7CR is in libapp.so (to see if same key used in mobile)
2. Inspect full outer content structure
3. Search for another decrypt function in the JS that handles {"iv":...,"value":...} format
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---- Part 1: Check libapp.so for ch7CR ----
print('=== Checking libapp.so for key fragments ===')
import os
lib_path = None
# Find libapp.so
for root, dirs, files in os.walk('apk_extracted'):
    for f in files:
        if f == 'libapp.so' and 'arm64' in root:
            lib_path = os.path.join(root, f)
            break
if not lib_path:
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f == 'libapp.so':
                lib_path = os.path.join(root, f)
                break

if lib_path:
    print(f'Found: {lib_path}')
    with open(lib_path, 'rb') as f:
        lib = f.read()
    for needle in [b'ch7CR', b'aa4uC', b'8KiBd', b'aa4uCch7CR8KiBdQ']:
        idx = lib.find(needle)
        print(f'  {needle}: {"found at " + str(idx) if idx >= 0 else "NOT FOUND"}')
else:
    print('libapp.so not found')

# ---- Part 2: Inspect outer content structure ----
print('\n=== Outer content structure ===')
import base64, requests
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
d = r.json()
content = d['data']['content']
outer = base64.b64decode(content + '==')
# Find all '"' positions
print(f'outer length: {len(outer)}')
sep = b'","value":"'
p2 = outer.find(sep); vs = p2 + len(sep)
ct_end = outer.find(b'"', vs)
print(f'p2={p2}, vs={vs}, ct_end={ct_end}')
print(f'outer[ct_end:ct_end+20]: {outer[ct_end:ct_end+20]!r}')
print(f'outer[ct_end-5:ct_end+5]: {outer[ct_end-5:ct_end+5]!r}')
# Check if there's more content after "
full_tail = outer[ct_end:]
print(f'outer tail (last 50): {outer[-50:]!r}')
print(f'outer tail hex: {outer[-20:].hex()}')
# Maybe there's a "tag" field
for needle in [b'"tag"', b'tag":', b'"auth"']:
    pos = outer.find(needle)
    if pos >= 0:
        print(f'Found {needle!r} at pos {pos}: {outer[pos:pos+50]!r}')

# ---- Part 3: Search JS for {"iv": or "value": handling ----
with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

print('\n=== JS: Search for iv/value content format ===')
# Look for patterns that process {"iv": or parse iv+value JSON
for pattern in [r'"iv"', r'value"', r'\.iv\b', r'iv_', r'parseIV', r'getIV']:
    matches = list(re.finditer(pattern, js))
    if matches:
        print(f'\nPattern {pattern!r}: {len(matches)} occurrences')
        for m in matches[:3]:
            print(f'  pos={m.start()}: {js[m.start()-30:m.start()+80]!r}')

# Look for the actual chapter decryptor: something that parses outer json
print('\n=== JS: patterns near "iv" AND "value" ===')
for m in re.finditer(r'"iv"', js):
    ctx = js[m.start()-100:m.start()+200]
    if 'value' in ctx and ('decrypt' in ctx.lower() or 'AES' in ctx or 'parse' in ctx):
        print(f'pos={m.start()}: {ctx!r}')
        print()
