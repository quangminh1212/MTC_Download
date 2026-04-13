"""
Inspect the full API response for chapter 21589884 and nearby chapters.
Look for any key, token, cipher, secret fields.
Also check other API endpoints.
"""
import sys, json, requests, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def pp(d, indent=0):
    """Pretty print dict/list structure showing keys and value types/previews."""
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                print('  '*indent + f'{k!r}: {type(v).__name__}')
                pp(v, indent+1)
            elif isinstance(v, str) and len(v) > 60:
                print('  '*indent + f'{k!r}: str(len={len(v)}) {v[:80]!r}...')
            else:
                print('  '*indent + f'{k!r}: {v!r}')
    elif isinstance(d, list):
        for i, v in enumerate(d[:3]):
            print('  '*indent + f'[{i}]:')
            pp(v, indent+1)
        if len(d) > 3:
            print('  '*indent + f'...({len(d)-3} more items)')

headers = {
    'User-Agent': 'Meta Novel App - Android',
    'Accept': 'application/json',
}

print('=== Chapter API response structure ===')
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', headers=headers, timeout=15)
print(f'Status: {r.status_code}')
print(f'Response headers: {dict(r.headers)}')
d = r.json()
pp(d)

print('\n=== Full response keys at all levels ===')
def find_all_keys(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f'{path}.{k}' if path else k
            if isinstance(v, str) and 16 <= len(v) <= 64 and v.replace('+', '').replace('/', '').replace('=', '').isalnum():
                print(f'  Possible key: {new_path!r} = {v!r}')
            find_all_keys(v, new_path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_all_keys(v, f'{path}[{i}]')
find_all_keys(d)

print('\n=== Looking at data.data fields ===')
if 'data' in d and isinstance(d['data'], dict):
    for k, v in d['data'].items():
        if k != 'content':
            print(f'  {k!r}: {str(v)[:100]!r}')

print('\n=== Try fetching other book chapters ===')
for cid in [21589883, 21589885, 1234567]:
    try:
        r2 = requests.get(f'https://android.lonoapp.net/api/chapters/{cid}', headers=headers, timeout=10)
        if r2.status_code == 200:
            d2 = r2.json()
            if 'data' in d2:
                print(f'Chapter {cid}: fields = {list(d2["data"].keys())}')
    except:
        pass

print('\n=== Check other API endpoints ===')
for endpoint in ['/api/books', '/api/stories', '/api/decrypt-key', '/api/content-key', '/api/config', '/api/app-config']:
    try:
        r3 = requests.get(f'https://android.lonoapp.net{endpoint}', headers=headers, timeout=5)
        print(f'{endpoint}: status={r3.status_code}')
    except Exception as e:
        print(f'{endpoint}: error={e}')
