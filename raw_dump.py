import requests, base64
import urllib3; urllib3.disable_warnings()

PROXY = {'https': 'http://127.0.0.1:8081'}

r = requests.get('https://android.lonoapp.net/api/chapters/21589884', verify=False, proxies=PROXY, timeout=15)
content = r.json()['data']['content']
print('content[:80]:', repr(content[:80]))

try:
    outer = base64.b64decode(content)
except Exception:
    outer = base64.b64decode(content + '==')

print('outer total:', len(outer), 'bytes')
print()

print('Byte-by-byte dump of first 80 bytes:')
for i, b in enumerate(outer[:80]):
    ch = chr(b) if 32 <= b < 127 else '.'
    print(f'  [{i:3d}] 0x{b:02x} = {ch!r}')

print()
# Find separator positions manually
sep = b'","value":"'
for i in range(len(outer) - len(sep)):
    if outer[i:i+len(sep)] == sep:
        print(f'Separator "","value":"" found at pos {i}')
        print(f'=> iv_field = outer[7:{i}] = {i-7} bytes')
        iv = outer[7:i]
        print(f'iv hex: {iv.hex()}')
        break
