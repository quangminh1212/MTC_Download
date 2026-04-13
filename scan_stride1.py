"""
Optimized stride-1 scan of libapp.so for AES key.
Use 2 chapters for cross-validation - a key must pass padding check on BOTH.
False positive rate: ~1/256 per chapter. Two chapters: ~1/65536.
For 10M candidates, expect <200 false positives → all verified quickly.
"""
import sys, base64, hmac, hashlib, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from Crypto.Cipher import AES
import os

def get_chapter_data(cid):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{cid}', timeout=15)
    content_str = r.json()['data']['content']
    pad = '=' * (-len(content_str) % 4)
    outer = base64.b64decode(content_str + pad)
    sep = b'","value":"'
    p2 = outer.find(sep); vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv_raw = outer[7:p2]; val_b64 = outer[vs:ct_end]
    mac_s = outer.find(b'"mac":"'); mac_e = outer.find(b'"', mac_s+7)
    mac_hex = outer[mac_s+7:mac_e].decode('ascii')
    ct = base64.b64decode(val_b64 + b'==')
    return {'iv_raw': iv_raw, 'val_b64': val_b64, 'mac_hex': mac_hex, 
            'ct': ct, 'ct_last': ct[-16:], 'ct_prev': ct[-32:-16]}

print('Fetching 2 chapters for cross-validation...')
c1 = get_chapter_data(21589884)
c2 = get_chapter_data(21598093)  # next chapter
print(f'c1: ct={len(c1["ct"])}B mac={c1["mac_hex"][:16]}...')
print(f'c2: ct={len(c2["ct"])}B mac={c2["mac_hex"][:16]}...')

# Precompute ECB check blocks
ct_last1, ct_prev1 = c1['ct_last'], c1['ct_prev']
ct_last2, ct_prev2 = c2['ct_last'], c2['ct_prev']

def check_padding(key_bytes):
    """Return True if key gives valid PKCS7 for BOTH chapters."""
    try:
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        dec1 = ecb.decrypt(ct_last1)
        last_pt1 = bytes(a^b for a,b in zip(dec1, ct_prev1))
        pv1 = last_pt1[-1]
        if not (1 <= pv1 <= 16 and all(b == pv1 for b in last_pt1[-pv1:])):
            return False
        # Confirmed valid for c1, now check c2
        ecb2 = AES.new(key_bytes, AES.MODE_ECB)
        dec2 = ecb2.decrypt(ct_last2)
        last_pt2 = bytes(a^b for a,b in zip(dec2, ct_prev2))
        pv2 = last_pt2[-1]
        return 1 <= pv2 <= 16 and all(b == pv2 for b in last_pt2[-pv2:])
    except:
        return False

def full_verify(key_bytes, chdata):
    """Full decrypt + MAC verify a chapter."""
    results = {}
    # Check MAC (both raw_iv and b64_iv forms)
    for iv_form, iv_used in [('raw', chdata['iv_raw']), ('b64', base64.b64encode(chdata['iv_raw']))]:
        data = iv_used + chdata['val_b64']
        h = hmac.new(key_bytes, data, hashlib.sha256).hexdigest()
        if h == chdata['mac_hex']:
            results[f'mac_{iv_form}'] = True
    # Decrypt
    for iv_name, iv_bytes in [('raw16', chdata['iv_raw'][:16]), ('zeros', bytes(16))]:
        try:
            c = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            pt = c.decrypt(chdata['ct'])
            pv = pt[-1]
            if 1 <= pv <= 16 and all(b == pv for b in pt[-pv:]):
                try:
                    text = pt[:-pv].decode('utf-8')[:80]
                    results[f'decrypt_{iv_name}'] = text
                except Exception as e:
                    results[f'decrypt_{iv_name}_raw'] = pt[:80].hex()
        except Exception as e:
            pass
    return results

# ---- Scan libapp.so ----
lib_path = r'.\libapp_extracted\libapp.so'
if not os.path.exists(lib_path):
    print('ERROR: libapp.so not found'); sys.exit(1)

with open(lib_path, 'rb') as f:
    lib = f.read()
print(f'\nlibapp.so: {len(lib)} bytes')
print(f'Scanning ALL {len(lib)-32} positions for AES-128 (stride=1)...')

hits_16 = []
hits_32 = []
REPORT_INTERVAL = 500_000

for off in range(0, len(lib)-32):
    if off % REPORT_INTERVAL == 0 and off > 0:
        print(f'  {off//1_000_000}M/{len(lib)//1_000_000}M  hits16={len(hits_16)}  hits32={len(hits_32)}')
    
    # AES-128: 16-byte key
    key16 = lib[off:off+16]
    if check_padding(key16):
        hits_16.append(off)
        print(f'  ** AES-128 CANDIDATE at offset {off}: {key16.hex()} = {key16!r}')
        res = full_verify(key16, c1)
        if res:
            print(f'     c1 verify: {res}')
        res2 = full_verify(key16, c2)
        if res2:
            print(f'     c2 verify: {res2}')

print(f'\nAES-128 total hits: {len(hits_16)}')

# AES-256 scan
print(f'\nScanning for AES-256 (stride=1)...')
for off in range(0, len(lib)-32):
    if off % REPORT_INTERVAL == 0 and off > 0:
        print(f'  {off//1_000_000}M/{len(lib)//1_000_000}M  hits32={len(hits_32)}')
    
    key32 = lib[off:off+32]
    try:
        ecb = AES.new(key32, AES.MODE_ECB)
        dec1 = ecb.decrypt(ct_last1)
        last_pt1 = bytes(a^b for a,b in zip(dec1, ct_prev1))
        pv1 = last_pt1[-1]
        if 1 <= pv1 <= 16 and all(b == pv1 for b in last_pt1[-pv1:]):
            # Check c2
            ecb2 = AES.new(key32, AES.MODE_ECB)
            dec2 = ecb2.decrypt(ct_last2)
            last_pt2 = bytes(a^b for a,b in zip(dec2, ct_prev2))
            pv2 = last_pt2[-1]
            if 1 <= pv2 <= 16 and all(b == pv2 for b in last_pt2[-pv2:]):
                hits_32.append(off)
                print(f'  ** AES-256 CANDIDATE at offset {off}: {key32.hex()}')
                res = full_verify(key32, c1)
                if res: print(f'     c1 verify: {res}')
    except:
        pass

print(f'AES-256 total hits: {len(hits_32)}')
print('\nDone.')
