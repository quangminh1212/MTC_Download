"""
Carefully analyze the chapter content encryption format.
Fetch a chapter and do byte-by-byte analysis to understand the structure.
"""
import requests, base64, json, sys, struct
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://android.lonoapp.net/api'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'NovelFeverApp/1.0'}

# Fetch a known chapter
r = requests.get(f'{BASE}/chapters/21589884', headers=HEADERS, timeout=10)
data = r.json()['data']

chapter_id = data['id']
chapter_name = data['name']
raw_content = data['content']
is_locked = data.get('is_locked', '?')

print(f"Chapter {chapter_id}: {chapter_name}")
print(f"is_locked: {is_locked}")
print(f"content (field length): {len(raw_content)} chars")
print()

# Decode from base64
content_bytes = base64.b64decode(raw_content + '==')  # fix padding
print(f"Decoded bytes: {len(content_bytes)} bytes")
print()

# Show first 100 bytes as hex
print("First 100 bytes (hex):")
print(' '.join(f'{b:02x}' for b in content_bytes[:100]))
print()

# Show first 100 bytes as ASCII (replacing non-printable)
print("First 100 bytes (ASCII):")
ascii_view = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02x}]' for b in content_bytes[:100])
print(ascii_view)
print()

# Find key positions
start_str = b'{"iv":"'
start_pos = content_bytes.find(start_str) 
print(f'Position of iv: offset {start_pos}')

if start_pos != -1:
    iv_start = start_pos + len(start_str)
    # Find the end of the iv field - look for ", "value":
    value_sep = b'","value":"'
    value_pos = content_bytes.find(value_sep, iv_start)
    print(f'Position of "value": offset {value_pos}')
    
    if value_pos != -1:
        iv_raw = content_bytes[iv_start:value_pos]
        print(f'\nIV raw bytes ({len(iv_raw)} bytes):')
        print(' '.join(f'{b:02x}' for b in iv_raw))
        print(f'IV as latin-1: {iv_raw.decode("latin-1")!r}')
        
        # Extract value field
        value_start = value_pos + len(value_sep)
        end_pos = content_bytes.find(b'"}', value_start)
        print(f'\nValue field: offset {value_start} to {end_pos}')
        
        if end_pos != -1:
            value_b64 = content_bytes[value_start:end_pos]
            print(f'Value base64 length: {len(value_b64)} chars')
            value_bytes = base64.b64decode(value_b64)
            print(f'Value decoded bytes: {len(value_bytes)} bytes')
            print(f'Value bytes / 16 = {len(value_bytes)/16:.2f} (should be integer for AES-CBC)')
            
            print(f'\nFirst 32 bytes of ciphertext:')
            print(' '.join(f'{b:02x}' for b in value_bytes[:32]))
        
        # Try to interpret the IV:
        print(f'\nIV interpretations:')
        print(f'1. First 16 bytes: {iv_raw[:16].hex()}')
        print(f'2. Last 16 bytes: {iv_raw[-16:].hex()}')
        # Try base64 decode on printable portions
        printable_iv = bytes([b for b in iv_raw if 32 <= b < 127])
        print(f'3. Printable bytes only ({len(printable_iv)}): {printable_iv!r}')
        
        # Try just the base64-looking part at the end
        import re
        b64_matches = re.findall(rb'[A-Za-z0-9+/]{4,}={0,2}', iv_raw)
        for m in b64_matches:
            try:
                dec = base64.b64decode(m + b'=' * ((-len(m)) % 4))
                print(f'4. Base64 "{m.decode()}" -> {len(dec)} bytes: {dec.hex()}')
            except:
                pass

print()
print("="*60)
print("Check if this could be the aes_crypt binary format...")
# aes_crypt format starts with AES magic: 
print(f"First bytes: {content_bytes[:3]!r}")

# Could the content be a JWT or similar?
if content_bytes[:1] == b'e' or b'.' in content_bytes[:50]:
    parts = content_bytes.split(b'.')
    print(f"JWT-like: {len(parts)} parts")
