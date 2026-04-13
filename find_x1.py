"""Find the REAL x1 string array in the JS file."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

print(f'JS length: {len(js)}')

# Find all occurrences of x1 patterns
print('\n--- All x1 references ---')
for m in re.finditer(r'x1[^\s(;,)]', js):
    pass  # too many

# Find 'return x1=' pattern
print('\n--- x1 assignment patterns ---')
for m in re.finditer(r'return x1=', js):
    ctx = js[max(0,m.start()-200):m.end()+100]
    print(f'pos={m.start()}: ...{ctx[180:]}...')
    print('---')

# Find function definitions containing x1
print('\n--- Functions with x1 in body ---')
funcs = re.finditer(r'function\s+\w+\(\)\s*\{[^\{]{0,5000}x1[^\}]{0,200}\}', js)
for i, m in enumerate(funcs):
    if i > 5: break
    body = m.group()
    if 'return' in body and ('x1=' in body or '"' in body):
        print(f'pos={m.start()}: {body[:400]}')
        print('---')

# Find: large chunks of quoted strings
print('\n--- Large quote chunks ---')
# Find positions where we have at least 30 consecutive quoted strings
for m in re.finditer(r'("[^"]{0,30}",\s*){30,}', js):
    print(f'pos={m.start()}: len={len(m.group())}, preview={m.group()[:200]}')
    print()
