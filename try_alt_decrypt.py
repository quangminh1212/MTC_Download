"""Try alternative decryption methods and look for key near AesCrypt in binary."""
import requests, base64, json, struct, zlib, sys, gzip, io
sys.stdout.reconfigure(encoding='utf-8')
import urllib3; urllib3.disable_warnings()

BASE = 'https://android.lonoapp.net/api'
PROXY = {'https': 'http://127.0.0.1:8081'}
SESS = requests.Session()
SESS.verify = False

# Get chapter 1 of a book we have in public listing
# Use an arbitrary known public chapter
print("Fetching chapter content...")
r = SESS.get(f'{BASE}/chapters/21589884', timeout=15, proxies=PROXY)
data = r.json()
raw_content = data.get('content', '')
ch_name = data.get('name', '?')
print(f"Chapter: {ch_name}")
print(f"Content field length: {len(raw_content)} chars")

# Decode outer base64
outer_bytes = base64.b64decode(raw_content + '==')
print(f"Outer base64 decoded: {len(outer_bytes)} bytes")
print(f"First 60 bytes: {outer_bytes[:60]}")
print(f"First 60 chars (latin1): {outer_bytes[:60].decode('latin-1')}")

# Parse as JSON (treating as latin-1 or unicode)
try:
    json_str = outer_bytes.decode('utf-8', errors='replace')
    obj = json.loads(json_str)
    iv_val = obj['iv']
    value_val = obj['value']
    print(f"\nJSON parsed OK")
    print(f"iv field type: {type(iv_val)}, len: {len(iv_val)}")
    print(f"value field type: {type(value_val)}, len: {len(value_val)}")
    
    # The iv field - what encoding?
    iv_bytes = iv_val.encode('latin-1') if isinstance(iv_val, str) else iv_val
    print(f"iv as bytes: {iv_bytes.hex()}")
    
    # Decode value field as base64
    try:
        # Add padding if needed
        padded = value_val + '=' * ((4 - len(value_val) % 4) % 4)
        ciphertext = base64.b64decode(padded)
        print(f"ciphertext: {len(ciphertext)} bytes, first 16: {ciphertext[:16].hex()}")
    except Exception as e:
        print(f"Value b64 decode error: {e}")
        ciphertext = None
        
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}")
    ciphertext = None

# Try: what if the VALUE is NOT AES but compressed?
if ciphertext:
    print(f"\n--- Testing non-AES decryption ---")
    
    # Test 1: Is ciphertext gzipped?
    try:
        decompressed = gzip.decompress(ciphertext)
        text = decompressed.decode('utf-8', errors='replace')
        print(f"GZIP decompressed: {len(decompressed)} bytes")
        print(f"  First 200 chars: {text[:200]}")
    except:
        print("Not gzip")
    
    # Test 2: Is ciphertext zlib?
    try:
        decompressed = zlib.decompress(ciphertext)
        text = decompressed.decode('utf-8', errors='replace')
        print(f"ZLIB decompressed: {len(decompressed)} bytes")
        print(f"  First 200 chars: {text[:200]}")
    except:
        print("Not zlib")
    
    # Test 3: XOR with common keys
    common_keys = [
        b'lonoapp', b'novelfever', b'novel', b'secret', 
        b'MTCNovel', b'android', b'flutter', b'dart',
        b'1234567890abcdef', b'abcdefghijklmnop',
    ]
    print("\nXOR tests (first 50 chars of result):")
    for key in common_keys:
        result = bytes([ciphertext[i] ^ key[i % len(key)] for i in range(min(200, len(ciphertext)))])
        text = result.decode('utf-8', errors='replace')
        # Check if result has readable Vietnamese
        readable = sum(1 for c in text if c.isalpha() or c in ' .,!?;:')
        if readable > 100:
            print(f"  XOR key={key}: READABLE! First 100: {text[:100]}")
        # else just show a bit
        elif readable > 50:
            print(f"  XOR key={key}: partial: {text[:50]}")
    
    # Test 4: What if value is just base64(plain_text) without any encryption?
    try:
        direct = base64.b64decode(value_val + '==').decode('utf-8', errors='replace')
        readable = sum(1 for c in direct if c.isalpha())
        if readable > 0.7 * len(direct[:200]):
            print(f"\nDirect base64 decode IS READABLE: {direct[:200]}")
        else:
            print(f"\nDirect base64 decode still garbled: {direct[:50]}")
    except Exception as e:
        print(f"Direct decode error: {e}")
    
    # Test 5: Treat ciphertext as RC4 with common keys
    def rc4(key, data):
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
        i = j = 0
        result = []
        for byte in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            result.append(byte ^ S[(S[i] + S[j]) % 256])
        return bytes(result)
    
    print("\nRC4 tests:")
    for key in [b'lonoapp', b'novelfever', b'secret', b'1234567890abcdef']:
        result = rc4(key, ciphertext[:300])
        text = result.decode('utf-8', errors='replace')
        readable = sum(1 for c in text if c.isalpha())
        if readable > 150:
            print(f"  RC4 key={key}: READABLE! {text[:100]}")

print("\nDone.")
