"""
Check whether the content field uses standard or URL-safe base64,
and verify IV extraction correctness.
"""
import base64, re, requests, json

URL = "https://android.lonoapp.net/api/chapters/21589884"
HEADERS = {"User-Agent": "okhttp/4.9.1", "Accept-Encoding": "gzip"}

r = requests.get(URL, headers=HEADERS, timeout=10)
data = r.json()
content = data['data']['content']

print(f"content length: {len(content)}")
print(f"content[0:80]: {content[:80]}")
print()
print(f"Chars in content that are URL-safe but not standard b64:")
url_only = [c for c in content if c in '-_']
print(f"  '-' count: {content.count('-')}")
print(f"  '_' count: {content.count('_')}")
print()

# Try standard b64
outer_std = base64.b64decode(content + "==")
print(f"Standard b64 decode -> {len(outer_std)} bytes")
print(f"  First 60 bytes: {outer_std[:60]}")
try:
    outer_std_str = outer_std.decode('ascii')
    print(f"  Is ASCII: YES")
    print(f"  As text: {outer_std_str[:100]}")
except:
    print(f"  Is ASCII: NO (contains binary bytes)")
print()

# Try URL-safe b64
outer_url = base64.urlsafe_b64decode(content + "==")
print(f"URL-safe b64 decode -> {len(outer_url)} bytes")
print(f"  First 60 bytes: {outer_url[:60]}")
try:
    outer_url_str = outer_url.decode('ascii')
    print(f"  Is ASCII: YES")
    print(f"  As text: {outer_url_str[:100]}")
    # Check if it's JSON
    parsed = json.loads(outer_url_str)
    print(f"  Is valid JSON: YES, keys: {list(parsed.keys())}")
    iv_val = parsed.get('iv','')
    print(f"  iv field: '{iv_val}' (len={len(iv_val)})")
    iv_raw = base64.b64decode(iv_val + "==")
    print(f"  iv decoded: {iv_raw.hex()} ({len(iv_raw)} bytes)")
except Exception as e:
    print(f"  Error: {e}")
print()

# Try standard b64 without padding
for pad in ['', '=', '==']:
    try:
        tmp = base64.b64decode(content + pad)
        if tmp[:7] == b'{"iv":"':
            print(f"Standard b64 with pad '{pad}' -> valid JSON prefix!")
    except:
        pass

# Try urlsafe without padding  
for pad in ['', '=', '==']:
    try:
        tmp = base64.urlsafe_b64decode(content + pad)
        if tmp[:7] == b'{"iv":"':
            print(f"URL-safe b64 with pad '{pad}' -> valid JSON prefix!")
    except:
        pass
