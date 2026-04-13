"""
Scan .text section of libapp.so (6.3MB, offset=0x410000) stride=1
for AES-128/256 key candidates with cross-validation against 2 different book chapters.
Expected false positives: ~96 for 6.3M candidates.
"""
import sys, base64, hmac, hashlib, struct, requests, json, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from Crypto.Cipher import AES

LIBPATH = r'C:\Dev\MTC_Download\libapp_extracted\libapp.so'
TEXT_OFFSET = 0x410000
TEXT_SIZE   = 6287248

def get_chapter_data(cid):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{cid}', timeout=15)
    d = r.json()
    if 'data' not in d: return None
    chap = d['data']
    content_str = chap.get('content','')
    if not content_str: return None
    pad = '=' * (-len(content_str) % 4)
    outer = base64.b64decode(content_str + pad)
    sep = b'","value":"'
    p2 = outer.find(sep); vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv_raw = outer[7:p2]
    val_b64 = outer[vs:ct_end]
    mac_s = outer.find(b'"mac":"'); mac_e = outer.find(b'"', mac_s+7)
    mac_hex = outer[mac_s+7:mac_e].decode('ascii')
    ct = base64.b64decode(val_b64 + b'==')
    return {'iv_raw': iv_raw, 'val_b64': val_b64, 'mac_hex': mac_hex,
            'ct': ct, 'book_id': chap.get('book_id')}

def verify_key_full(key_bytes, chdata):
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
                except: results[f'dec_{iv_name}_raw'] = pt[:80].hex()
        except: pass
    return results

print('Fetching chapter data...')
c1 = get_chapter_data(21589884)  # book 139039
c2 = get_chapter_data(22204525)  # book 140643 (DIFFERENT)
print(f'c1: book={c1["book_id"]} mac={c1["mac_hex"][:20]}')
print(f'c2: book={c2["book_id"]} mac={c2["mac_hex"][:20]}')

print(f'\nLoading libapp.so .text section: offset=0x{TEXT_OFFSET:x} size={TEXT_SIZE:,}B')
with open(LIBPATH, 'rb') as f:
    f.seek(TEXT_OFFSET)
    text_section = f.read(TEXT_SIZE)
print(f'Loaded {len(text_section):,} bytes from .text')

def scan_section(data, label, key_len):
    hits = []
    total = len(data)
    t0 = time.time()
    mac1 = c1['mac_hex'][:8]
    mac2 = c2['mac_hex'][:8]

    for i in range(total - key_len + 1):
        if i % 100000 == 0:
            elapsed = time.time() - t0
            pct = 100.0*i/total
            rate = i/elapsed if elapsed > 0 else 0
            eta = (total-i)/rate if rate > 0 else 0
            print(f'\r  AES-{key_len*8} .text {label}: {pct:.1f}% '
                  f'({i:,}/{total:,}) rate={rate/1000:.0f}K/s eta={eta:.0f}s '
                  f'hits={len(hits)}', end='', flush=True)

        key = data[i:i+key_len]

        # Quick MAC filter on c1 only (cheap vs AES)
        h1 = hmac.new(key, c1['iv_raw'] + c1['val_b64'], hashlib.sha256).hexdigest()
        if h1 == c1['mac_hex']:
            # Full verification
            r1 = verify_key_full(key, c1)
            r2 = verify_key_full(key, c2)
            print(f'\n  *** HIT at 0x{TEXT_OFFSET+i:x}: key={key.hex()}')
            print(f'      c1 results: {r1}')
            print(f'      c2 results: {r2}')
            hits.append({'offset': i, 'key': key.hex(), 'r1': r1, 'r2': r2})
        else:
            # Also test b64(iv) form
            h1b = hmac.new(key, base64.b64encode(c1['iv_raw']) + c1['val_b64'], hashlib.sha256).hexdigest()
            if h1b == c1['mac_hex']:
                r1 = verify_key_full(key, c1)
                r2 = verify_key_full(key, c2)
                print(f'\n  *** HIT(b64iv) at 0x{TEXT_OFFSET+i:x}: key={key.hex()}')
                print(f'      c1 results: {r1}')
                print(f'      c2 results: {r2}')
                hits.append({'offset': i, 'key': key.hex(), 'r1': r1, 'r2': r2})

    elapsed = time.time() - t0
    print(f'\r  AES-{key_len*8} .text scan complete: {total:,} bytes in {elapsed:.0f}s, '
          f'hits={len(hits)}                                  ')
    return hits

hits16 = scan_section(text_section, '.text', 16)
print(f'\nAES-128 total hits: {len(hits16)}')
for h in hits16:
    print(f'  0x{TEXT_OFFSET+h["offset"]:x}: {h}')

hits32 = scan_section(text_section, '.text', 32)
print(f'\nAES-256 total hits: {len(hits32)}')
for h in hits32:
    print(f'  0x{TEXT_OFFSET+h["offset"]:x}: {h}')

print('\nDone scanning .text section.')
