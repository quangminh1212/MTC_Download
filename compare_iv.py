"""Compare cached chapter response from mitm vs fresh request - to determine if IV is static or random."""
import sys, base64
sys.stdout.reconfigure(encoding='utf-8')

from mitmproxy.io import FlowReader

# Get cached response from mitm
flows = []
with open('mitm_capture.bin', 'rb') as f:
    reader = FlowReader(f)
    for flow in reader.stream():
        flows.append(flow)

# Find first chapter 21589884 response
cached_content = None
for flow in flows:
    if not hasattr(flow, 'request'): continue
    if '21589884' in flow.request.pretty_url and flow.response:
        import json
        try:
            resp_json = json.loads(flow.response.text)
            cached_content = resp_json['data']['content']
            print(f'Got cached content from mitm: len={len(cached_content)}')
            break
        except:
            print('JSON parse error')

if cached_content:
    # Decode the outer base64
    outer = base64.b64decode(cached_content + '==')
    sep = b'","value":"'
    pos = outer.find(sep)
    iv_field = outer[7:pos]
    print(f'Cached IV field (36 bytes): {iv_field.hex()}')
    print(f'Cached IV[:16]: {iv_field[:16].hex()}')

import requests, urllib3; urllib3.disable_warnings()

PROXY = {'https': 'http://127.0.0.1:8081'}
print('\nFetching fresh response...')
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', verify=False, proxies=PROXY, timeout=15)
fresh_content = r.json()['data']['content']
outer2 = base64.b64decode(fresh_content + '==')
pos2 = outer2.find(sep)
iv2 = outer2[7:pos2]
print(f'Fresh IV field (36 bytes): {iv2.hex()}')
print(f'Fresh IV[:16]: {iv2[:16].hex()}')

if cached_content and iv_field.hex() == iv2.hex():
    print('\n*** IVs are IDENTICAL - server caches the encryption!')
    print('=> Same ciphertext + IV every time. Can use any captured response to decrypt.')
else:
    print('\n*** IVs are DIFFERENT - server re-encrypts each request!')

# Also compare ciphertext lengths
outer1 = base64.b64decode(cached_content + '==')
pos1 = outer1.find(sep)
ct_b64_1 = outer1[pos1 + len(sep):-2]
ct1 = base64.b64decode(ct_b64_1 + b'==')
ct_b64_2 = outer2[pos2 + len(sep):-2]
ct2 = base64.b64decode(ct_b64_2 + b'==')
print(f'\nCached CT len: {len(ct1)}, Fresh CT len: {len(ct2)}')
print(f'CT same: {ct1 == ct2}')
