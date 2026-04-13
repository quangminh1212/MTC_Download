"""
Scan .rodata section (4.2MB) of libapp.so with stride=1 for AES key.
Cross-validate across 2 chapters from DIFFERENT books.
"""
import sys, base64, hmac, hashlib, requests, struct, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from Crypto.Cipher import AES

def get_chapter_data(cid):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{cid}', timeout=15)
    d = r.json()
    if 'data' not in d:
        print(f'  FAILED {cid}: {d}'); return None
    chap = d['data']
    content_str = chap.get('content','')
    if not content_str:
        print(f'  No content {cid}'); return None
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
            'ct': ct, 'ct_last': ct[-16:], 'ct_prev': ct[-32:-16],
            'book_id': chap.get('book_id'), 'id': cid}

print('=== Fetching chapters ===')
# Book 1: 139039
c1 = get_chapter_data(21589884)
print(f'c1: book_id={c1["book_id"]} mac={c1["mac_hex"][:20]}... ct={len(c1["ct"])}B')

# Book 2: 140643 (different book, first_chapter=22204525)
c2 = get_chapter_data(22204525)
if c2:
    print(f'c2: book_id={c2["book_id"]} mac={c2["mac_hex"][:20]}... ct={len(c2["ct"])}B')
    if c2['book_id'] != c1['book_id']:
        print('  --> DIFFERENT BOOKS - good for cross-validation')
    else:
        print('  --> Same book! Trying another chapter...')
        c2 = get_chapter_data(22204526)
        if c2: print(f'c2 (next): book_id={c2["book_id"]}')
else:
    # Try book 153347
    c2 = get_chapter_data(22200000)
    if not c2:
        # Fall back to same book, different chapter
        c2 = get_chapter_data(21598093)
        print(f'c2 fallback: book_id={c2["book_id"]} mac={c2["mac_hex"][:20]}...')

ct_last1, ct_prev1 = c1['ct_last'], c1['ct_prev']
ct_last2 = c2['ct_last'] if c2 else c1['ct_last']
ct_prev2 = c2['ct_prev'] if c2 else c1['ct_prev']
diff_books = c2 and c2['book_id'] != c1['book_id']
print(f'\nCross-validation: different_books={diff_books}')

def verify_key_full(key_bytes, chdata):
    """Try MAC verification and AES decrypt."""
    results = {}
    for iv_form, iv_used in [('raw', chdata['iv_raw']), ('b64', base64.b64encode(chdata['iv_raw']))]:
        h = hmac.new(key_bytes, iv_used + chdata['val_b64'], hashlib.sha256).hexdigest()
        if h == chdata['mac_hex']:
            results[f'MAC_{iv_form}'] = True
    for iv_name, iv_bytes in [('raw16', chdata['iv_raw'][:16]), ('zeros', bytes(16))]:
        try:
            c = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            pt = c.decrypt(chdata['ct'])
            pv = pt[-1]
            if 1 <= pv <= 16 and all(b == pv for b in pt[-pv:]):
                try: results[f'dec_{iv_name}'] = pt[:-pv].decode('utf-8')[:80]
                except Exception as e:
                    results[f'dec_{iv_name}_raw'] = pt[:80].hex()
        except: pass
    return results

# ============================================================
# Load .rodata section
# ============================================================
print('\n=== Loading ELF .rodata ===')
lib_path = r'.\libapp_extracted\libapp.so'
with open(lib_path, 'rb') as f:
    lib = f.read()

# Read .rodata from ELF (offset=0x200, size=4246624)
rodata_offset = 0x200
rodata_size   = 4246624
rodata = lib[rodata_offset : rodata_offset + rodata_size]
print(f'.rodata: offset={rodata_offset:#x}, size={rodata_size:,}B ({rodata_size//1024}KB)')

def scan_section(section_bytes, sec_name, keylen, c1, c2=None):
    print(f'\n--- Scanning {sec_name} for AES-{keylen*8} (stride=1) ---')
    ct_last1, ct_prev1 = c1['ct_last'], c1['ct_prev']
    if c2:
        ct_last2, ct_prev2 = c2['ct_last'], c2['ct_prev']
    
    hits = []
    n = len(section_bytes) - keylen
    t0 = time.time()
    PROGRESS = max(1, n // 20)
    
    for off in range(n):
        if off % PROGRESS == 0:
            elapsed = time.time() - t0
            pct = off * 100 // n
            speed = off / elapsed if elapsed > 0 else 0
            eta = (n - off) / speed if speed > 0 else 0
            print(f'  {pct}%  off={off//1024}KB  hits={len(hits)}  {speed/1000:.0f}K/s  ETA={eta:.0f}s')
        
        key = section_bytes[off:off+keylen]
        # Fast check: decrypt last block (ECB mode = ignore CBC chain for just padding check)
        try:
            ecb = AES.new(key, AES.MODE_ECB)
            dec1 = ecb.decrypt(ct_last1)
            pt1 = bytes(a^b for a,b in zip(dec1, ct_prev1))
            pv1 = pt1[-1]
            if not (1 <= pv1 <= 16 and all(b == pv1 for b in pt1[-pv1:])):
                continue
            # c1 passes! Check c2
            if c2:
                ecb2 = AES.new(key, AES.MODE_ECB)
                dec2 = ecb2.decrypt(ct_last2)
                pt2 = bytes(a^b for a,b in zip(dec2, ct_prev2))
                pv2 = pt2[-1]
                if not (1 <= pv2 <= 16 and all(b == pv2 for b in pt2[-pv2:])):
                    continue
        except:
            continue
        
        hits.append(off)
        print(f'\n*** AES-{keylen*8} HIT at offset {off} (rodata+{off:#x}): {key.hex()} = {key!r}')
        
        # Full verification
        res1 = verify_key_full(key, c1)
        print(f'    c1 verify: {res1}')
        if c2:
            res2 = verify_key_full(key, c2)
            print(f'    c2 verify: {res2}')
        
        if 'MAC_raw' in res1 or 'MAC_b64' in res1:
            print(f'\n!!! CONFIRMED KEY (MAC match): {key.hex()}')
            print(f'    As string: {key!r}')
    
    elapsed = time.time() - t0
    print(f'\n  Done: {n:,} candidates in {elapsed:.1f}s ({n/elapsed/1000:.1f}K/s), hits={len(hits)}')
    return hits

# Scan .rodata with AES-128
hits16 = scan_section(rodata, '.rodata', 16, c1, c2)
print(f'\nAES-128 total hits: {len(hits16)}')

# Scan .rodata with AES-256
hits32 = scan_section(rodata, '.rodata', 32, c1, c2)
print(f'\nAES-256 total hits: {len(hits32)}')

print('\n=== SUMMARY ===')
print(f'AES-128 hits: {len(hits16)}')
print(f'AES-256 hits: {len(hits32)}')
if not hits16 and not hits32:
    print('Key NOT found in .rodata section.')
    print('Next steps: scan full binary (libflutter.so, etc.) or check key derivation.')
