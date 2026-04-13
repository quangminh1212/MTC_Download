"""
Brute-force key search: 
1. Scan libapp.so with sliding 16-byte window (fast AES-ECB padding check)
2. Repeat for 32-byte window
3. Search APK assets/config files for key material
"""
import sys, base64, hmac, hashlib, os, re
from Crypto.Cipher import AES
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests

print('Fetching chapter...')
r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
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

# For AES padding check: compute what last plaintext block should look like
# AES-CBC: last_pt = AES_ECB_decrypt(key, ct[-16:]) XOR ct[-32:-16]
# For valid PKCS7: last byte pv in 1-16, all last pv bytes == pv
ct_last = ct[-16:]
ct_prev = ct[-32:-16]
print(f'ct[-16:] = {ct_last.hex()}')
print(f'ct[-32:-16] = {ct_prev.hex()}')
print(f'mac_hex = {mac_hex}')
print(f'iv_raw = {iv_raw.hex()}')

def check_mac(k_bytes, iv_raw, val_b64, expected_mac):
    data = iv_raw + val_b64
    h = hmac.new(k_bytes, data, hashlib.sha256).hexdigest()
    if h == expected_mac: return 'raw_iv'
    data2 = base64.b64encode(iv_raw) + val_b64
    h2 = hmac.new(k_bytes, data2, hashlib.sha256).hexdigest()
    if h2 == expected_mac: return 'b64_iv'
    return None

def final_check(k_bytes):
    """Full decrypt check on candidate key."""
    mac_form = check_mac(k_bytes, iv_raw, val_b64, mac_hex)
    # Try decrypt
    for iv_try in [iv_raw[:16], bytes(16)]:
        try:
            c = AES.new(k_bytes, AES.MODE_CBC, iv_try)
            pt = c.decrypt(ct)
            pv = pt[-1]
            if 1 <= pv <= 16 and all(b == pv for b in pt[-pv:]):
                try:
                    text = pt[:-pv].decode('utf-8')[:80]
                    return f'DECRYPT+{iv_try.hex()[:8]}', text
                except: pass
        except: pass
    if mac_form:
        return f'MAC_ONLY+{mac_form}', None
    return None, None

# ---- AES-128 padding check (fast) ----
def ecb_last_ok(key16):
    """Check if last CT block has valid PKCS7 padding with this key."""
    try:
        ecb = AES.new(key16, AES.MODE_ECB)
        dec = ecb.decrypt(ct_last)
        # XOR with prev block
        last_pt = bytes(a^b for a,b in zip(dec, ct_prev))
        pv = last_pt[-1]
        return 1 <= pv <= 16 and all(b == pv for b in last_pt[-pv:])
    except:
        return False

# Similarly for AES-256
def ecb_last_ok_256(key32):
    try:
        ecb = AES.new(key32, AES.MODE_ECB)
        dec = ecb.decrypt(ct_last)
        last_pt = bytes(a^b for a,b in zip(dec, ct_prev))
        pv = last_pt[-1]
        return 1 <= pv <= 16 and all(b == pv for b in last_pt[-pv:])
    except:
        return False

# ---- Scan libapp.so ----
lib_path = r'.\libapp_extracted\libapp.so'
if os.path.exists(lib_path):
    print(f'\n=== Scanning libapp.so for AES-128 keys ===')
    with open(lib_path, 'rb') as f:
        lib = f.read()
    
    count_128 = 0; count_256 = 0; hits_128 = []; hits_256 = []
    
    # Stride=1 (every byte) is thorough but ~10M iterations
    # Start with stride=1 aligned (every 16 bytes) then fall through to stride=1 if needed
    step = 16  # change to 1 for thorough
    for off in range(0, len(lib)-32, step):
        key16 = lib[off:off+16]
        if ecb_last_ok(key16):
            hits_128.append(off)
        if off % (step * 100000) == 0 and off > 0:
            print(f'  AES-128 progress: {off//1048576}MB/{len(lib)//1048576}MB, hits={len(hits_128)}')
    
    print(f'AES-128 hits (stride={step}): {len(hits_128)} at {hits_128[:20]}')
    
    if hits_128:
        print('  Verifying hits with full decrypt...')
        for off in hits_128[:20]:
            key16 = lib[off:off+16]
            result, text = final_check(key16)
            if result:
                print(f'  CONFIRMED at offset {off}: key={key16.hex()!r} result={result} text={text!r}')
    
    # AES-256 scan
    print(f'\n=== Scanning for AES-256 keys ===')
    for off in range(0, len(lib)-32, step):
        key32 = lib[off:off+32]
        if ecb_last_ok_256(key32):
            hits_256.append(off)
        if off % (step * 100000) == 0 and off > 0:
            print(f'  AES-256 progress: {off//1048576}MB/{len(lib)//1048576}MB, hits={len(hits_256)}')
    
    print(f'AES-256 hits (stride={step}): {len(hits_256)} at {hits_256[:20]}')

# ---- Scan APK assets ----
print('\n=== Scanning APK assets ===')
apk_dirs = [r'.\apk_extracted', r'.\apk']
for apk_dir in apk_dirs:
    if not os.path.exists(apk_dir):
        continue
    for root, dirs, files in os.walk(apk_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                fdata = open(fpath, 'rb').read()
            except: continue
            # Look for strings 16-64 chars that might be keys
            for m in re.finditer(rb'[A-Za-z0-9+/]{16,64}={0,2}', fdata):
                s = m.group()
                rel = os.path.relpath(fpath, apk_dir)
                # Try raw bytes (if 16/24/32 len)
                if len(s) in (16, 24, 32):
                    if ecb_last_ok(s[:16]) or (len(s) >= 32 and ecb_last_ok_256(s[:32])):
                        result, text = final_check(s[:len(s) if len(s) in (16,24,32) else 16])
                        if result:
                            print(f'ASSET HIT: {rel} offset={m.start()} key={s!r} result={result} text={text!r}')
                # Try base64 decode
                try:
                    bd = base64.b64decode(s + b'=' * (-len(s) % 4))
                    if len(bd) in (16, 24, 32):
                        kb = bd
                        if ecb_last_ok(kb[:16]) or (len(kb) == 32 and ecb_last_ok_256(kb)):
                            result, text = final_check(kb)
                            if result:
                                print(f'ASSET B64 HIT: {rel} offset={m.start()} decoded_key={kb.hex()} result={result} text={text!r}')
                except: pass

print('\nDone.')
