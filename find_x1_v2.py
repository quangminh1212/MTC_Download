"""Find function x1 definition and extract the full string array."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Find all function definitions named x1
print('=== function x1 definitions ===')
for m in re.finditer(r'function x1\b', js):
    pos = m.start()
    # Find end of function (matching braces)
    depth = 0
    start_func = pos
    i = pos
    while i < len(js):
        if js[i] == '{':
            depth += 1
        elif js[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    func_body = js[pos:i+1]
    print(f'pos={pos}, len={len(func_body)}: {func_body[:300]}')
    print(f'...last 200: {func_body[-200:]}')
    print('---')

# Extract the x1 array
print('\n=== Extracting x1 array ===')
m = re.search(r'function x1\b[^{]*\{(.+)\}', js[:35000])
if m:
    body = m.group(1)
    print(f'Body (first 500): {body[:500]}')
    # Find the array
    arr_match = re.search(r'\[([^\[\]]{200,})\]', body)
    if arr_match:
        arr_content = arr_match.group(1)
        entries = re.findall(r'"([^"]*)"', arr_content)
        print(f'Entries: {len(entries)}')
        print(f'All entries: {entries}')
else:
    print('No x1 function found in first 35000 chars')
    
# Try finding where x1 body actually is
print('\n=== x1 body location ===')
# search for the literal const x= pattern inside x1
for m in re.finditer(r'const x=\[', js):
    pos = m.start()
    # Extract the array
    arr_start = pos + len('const x=')
    # Find matching ]
    depth = 0
    i = arr_start
    while i < len(js):
        if js[i] == '[':
            depth += 1
        elif js[i] == ']':
            depth -= 1
            if depth == 0:
                break
        i += 1
    arr = js[arr_start:i+1]
    entries = re.findall(r'"([^"]*)"', arr)
    print(f'const x=[...] at pos={pos}: {len(entries)} entries')
    if 'ch7CR' in entries:
        idx = entries.index('ch7CR')
        print(f'  ch7CR at idx={idx}')
        print(f'  All entries: {entries}')
