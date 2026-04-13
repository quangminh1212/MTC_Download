"""
The outer JSON has: {"iv":"...","value":"...","mac":"61973dce0a5...","tag":""}
This is EXACTLY Laravel's Crypt::encrypt() format!
- iv = base64(random_bytes(16))
- value = base64(openssl_encrypt(...))  
- mac = hex(HMAC-SHA256(iv + value, key))
- tag = "" (not used in CBC mode)

Let's:
1. Inspect the raw content and outer properly
2. Check what the iv field ACTUALLY looks like (is it still base64?)
3. Try to use the MAC to verify/crack the key
"""
import sys, base64, json, requests, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
d = r.json()
content_str = d['data']['content']  # Python string

print(f'content_str type: {type(content_str)}')
print(f'content_str length: {len(content_str)}')
print(f'content_str first 50: {content_str[:50]!r}')
print(f'content_str last 10: {content_str[-10:]!r}')
print(f'content_str is pure ASCII: {all(ord(c) < 128 for c in content_str)}')
print(f'len % 4 = {len(content_str) % 4}')

# Proper padding
pad = '=' * (-len(content_str) % 4)
print(f'Need {len(pad)} padding chars')
outer = base64.b64decode(content_str + pad)
print(f'\nouter length: {len(outer)}')

# Now try to decode as UTF-8 to see if it's valid JSON
try:
    outer_str = outer.decode('utf-8')
    print('outer IS valid UTF-8')
    # Try JSON parse
    try:
        data = json.loads(outer_str)
        print('outer IS valid JSON')
        print(f'  keys: {list(data.keys())}')
        for k, v in data.items():
            print(f'  {k!r}: {str(v)[:80]!r}')
    except json.JSONDecodeError as e:
        print(f'outer is NOT valid JSON: {e}')
except UnicodeDecodeError as e:
    print(f'outer is NOT valid UTF-8: {e}')
    # Try to print as string with errors='replace'
    outer_str_rep = outer.decode('utf-8', errors='replace')
    print(f'outer (replace): {outer_str_rep[:200]!r}')
    
    # Find where the first non-UTF8 byte is
    for i, b in enumerate(outer):
        try:
            outer[i:i+1].decode('utf-8')
        except:
            if b < 0x80 or b > 0xbf:
                print(f'Bad byte at pos {i}: 0x{b:02x}  context: {outer[i-5:i+10].hex()}')
                if i > 30:
                    break

print('\n--- Finding fields manually ---')
# Find mac field
mac_start = outer.find(b'"mac":"')
if mac_start >= 0:
    mac_val_start = mac_start + 7
    mac_val_end = outer.find(b'"', mac_val_start)
    mac_hex = outer[mac_val_start:mac_val_end].decode('ascii')
    print(f'mac = {mac_hex!r}')
    print(f'mac length: {len(mac_hex)} chars (should be 64 for SHA256)')
else:
    print('mac field not found')

# Find tag field
tag_start = outer.find(b'"tag":"')
if tag_start >= 0:
    tag_val_start = tag_start + 7
    tag_val_end = outer.find(b'"', tag_val_start)
    tag_val = outer[tag_val_start:tag_val_end]
    print(f'tag = {tag_val!r}')

# Full iv field  
sep = b'","value":"'
p2 = outer.find(sep)
iv_raw = outer[7:p2]
print(f'\niv_raw length: {len(iv_raw)}')
print(f'iv_raw hex: {iv_raw.hex()}')
print(f'iv_raw printable: {iv_raw!r}')

# In Laravel: the json has iv as ASCII base64 string (all printable)
# Check if iv_raw contains only printable base64 chars
is_b64_printable = all(c in b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in iv_raw)
print(f'iv_raw is pure base64: {is_b64_printable}')

# The iv field should be base64 of 16 bytes = 24 chars
# Try to base64-decode the iv field
if is_b64_printable:
    iv_bytes = base64.b64decode(iv_raw + b'==' * (4 - len(iv_raw) % 4) if len(iv_raw) % 4 else iv_raw)
    print(f'iv_decoded: {iv_bytes.hex()} ({len(iv_bytes)} bytes)')
else:
    print('iv has non-base64 bytes - first 8 are ASCII, rest has binary')
    # Try: maybe the iv is just the first 16 bytes raw
    print(f'iv first 16 bytes: {iv_raw[:16].hex()}')
    print(f'iv: might be b64(iv_raw[:16]).rstrip("="): {base64.b64encode(iv_raw[:16]).decode()}')
