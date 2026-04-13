import requests, base64, sys, hashlib
import urllib3; urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

PROXY = {'https': 'http://127.0.0.1:8081'}

# Fetch multiple chapters to compare
CHAPTER_IDS = [21589884, 21598093, 21647009]

for ch_id in CHAPTER_IDS:
    print(f"\n{'='*60}")
    print(f"Chapter {ch_id}")
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{ch_id}', verify=False, proxies=PROXY, timeout=15)
    d = r.json()
    content = d['data']['content']
    
    try: outer = base64.b64decode(content)
    except: outer = base64.b64decode(content + '==')
    
    print(f'Outer total bytes: {len(outer)}')
    print(f'First 8 hex: {outer[:8].hex()} = {outer[:8]}')
    
    # Find separator
    sep = b'","value":"'
    pos = outer.find(sep)
    print(f'Separator pos: {pos}')
    
    iv_start = 8  # after {"iv":"
    iv_bytes = outer[iv_start:pos]
    print(f'IV field: {len(iv_bytes)} bytes')
    print(f'IV hex: {iv_bytes.hex()}')
    
    # Check last 4 bytes (should be == padding)
    print(f'IV last 4 bytes: {iv_bytes[-4:].hex()} = {iv_bytes[-4:]}')
    
    # Try treating first 16 as AES IV
    iv16 = iv_bytes[:16]
    print(f'IV[0:16]: {iv16.hex()}')
    
    # Try treating last 16 as AES IV
    ivlast16 = iv_bytes[-16:]
    print(f'IV[-16:]: {ivlast16.hex()}')
    
    # Extract ciphertext
    ct_start = pos + len(sep)
    ct_end = outer.rfind(b'"')
    ct_b64 = outer[ct_start:ct_end].decode('ascii')
    ct = base64.b64decode(ct_b64 + '==')
    print(f'Ciphertext: {len(ct)} bytes, {len(ct) % 16 == 0} (mod 16={len(ct) % 16})')
    print(f'CT first 32: {ct[:32].hex()}')

print("\n\nKey search in iv_bytes - checking if any 16-byte window decrypts to Vietnamese...")
