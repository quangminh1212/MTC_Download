"""Verify candidate keys with strict (no errors='replace') UTF-8 decode."""
import base64, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
content = r.json()['data']['content']
outer = base64.b64decode(content + '==')
sep = b'","value":"'
pos = outer.find(sep); vs = pos + len(sep)
ct_end = outer.find(b'"', vs)
iv16 = outer[7:23]
ct = base64.b64decode(outer[vs:ct_end] + b'==')
print(f'ct: {len(ct)}B, ct%16={len(ct)%16}')
print(f'iv16: {iv16.hex()}')
print()

candidates = {
    'libflutter.so': bytes.fromhex('0daaedfd27ad35ab62bde45eb2896f7a'),
    'libapp.bak':    bytes.fromhex('6acca7702a26a657ad7968ad8556a5b9'),
}

for name, key in candidates.items():
    print(f'--- {name}: {key.hex()} ---')
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv16)
        pt_padded = cipher.decrypt(ct)
        pt = unpad(pt_padded, 16)
        # Strict decode - raises UnicodeDecodeError if not valid UTF-8
        text = pt.decode('utf-8')
        print(f'  STRICT UTF-8: OK  ({len(text)} chars)')
        print(f'  First 200 chars: {text[:200]}')
        viet = sum(1 for c in text if '\u00C0' <= c <= '\u1EFF')
        print(f'  Vietnamese chars: {viet}')
    except UnicodeDecodeError as e:
        print(f'  STRICT UTF-8: FAILED ({e})')
        # Try lenient
        text = pt_padded.decode('utf-8', errors='replace')
        print(f'  Lenient first 50: {text[:50]!r}')  
    except Exception as e:
        print(f'  Error: {e}')
    print()
