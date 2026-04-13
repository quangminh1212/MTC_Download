"""
brute_key5.py - Search for base64-encoded or hex-encoded AES keys in native binaries.
Dart's encrypt package commonly uses Key.fromBase64('...') or Key.fromUtf8('...').
Key.fromBase64 stores the BASE64 STRING in libapp.so, not raw bytes.
Key.fromUtf8 stores a printable string. Both are covered here plus hex keys.
"""
import base64, re, sys, time, requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

LIBAPP = r'C:\Dev\MTC_Download\libapp_extracted\libapp.so'
CHAPTER_ID = 21589884

def fetch_and_parse():
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{CHAPTER_ID}', timeout=15)
    content = r.json()['data']['content']
    outer = base64.b64decode(content + '==')
    sep = b'","value":"'
    pos = outer.find(sep)
    vs = pos + len(sep)
    ct_end = outer.find(b'"', vs)
    iv16 = outer[7:23]
    ct = base64.b64decode(outer[vs:ct_end] + b'==')
    assert len(ct) % 16 == 0, f"ct%16 = {len(ct)%16}"
    print(f"  outer:{len(outer)}B  sep@{pos}  ct:{len(ct)}B  ct%16=0")
    return iv16, ct

def check_key(key_bytes, iv16, ct):
    """Returns True if key decrypts to valid Vietnamese text."""
    try:
        # Fast PKCS7 check on last block (no IV needed)
        ecb = AES.new(key_bytes, AES.MODE_ECB)
        last_plain = bytes(a ^ b for a, b in zip(
            ecb.decrypt(ct[-16:]), ct[-32:-16]))
        pad_v = last_plain[-1]
        if not (1 <= pad_v <= 16):
            return False
        if not all(last_plain[-pad_v:] == bytes([pad_v]) * pad_v):
            for b in last_plain[-pad_v:]:
                if b != pad_v: return False
        # Full CBC decrypt + UTF-8 check
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv16)
        pt = unpad(cipher.decrypt(ct), 16)
        s = pt.decode('utf-8', errors='replace')
        viet = sum(1 for c in s if '\u00C0' <= c <= '\u1EFF')
        return viet >= 10
    except Exception:
        return False

def scan_b64_keys(data, iv16, ct):
    """Extract and test all base64-decoded strings that yield 16/24/32 bytes."""
    # Valid base64 charset (standard + url-safe)
    B64_RE = re.compile(rb'[A-Za-z0-9+/\-_]{22,48}={0,2}')
    found = set()
    candidates = []
    for m in B64_RE.finditer(data):
        s = m.group()
        for variant in [s, s.replace(b'-', b'+').replace(b'_', b'/'),
                        s.replace(b'+', b'-').replace(b'/', b'_')]:
            for pad in [b'', b'=', b'==']:
                try:
                    decoded = base64.b64decode(variant + pad)
                    if len(decoded) in (16, 24, 32):
                        if decoded not in found:
                            found.add(decoded)
                            candidates.append(decoded)
                except Exception:
                    pass
    return candidates

def scan_hex_keys(data, iv16, ct):
    """Extract and test hex-encoded keys."""
    HEX_RE = re.compile(rb'[0-9a-fA-F]{32,64}')
    found = set()
    candidates = []
    for m in HEX_RE.finditer(data):
        s = m.group().decode()
        for length in (32, 48, 64):
            if len(s) == length:
                for i in range(0, min(4, len(s) - length + 1), 1):
                    sub = s[i:i+length]
                    try:
                        decoded = bytes.fromhex(sub)
                        if decoded not in found:
                            found.add(decoded)
                            candidates.append(decoded)
                    except Exception:
                        pass
    return candidates

if __name__ == '__main__':
    t0 = time.time()
    print(f"Scanning {LIBAPP}")
    data = open(LIBAPP, 'rb').read()
    print(f"  lib: {len(data):,}B")

    print("Fetching chapter...")
    iv16, ct = fetch_and_parse()
    print(f"  IV: {iv16.hex()}  CT: {len(ct)}B")

    print("\n--- Base64-encoded key scan ---")
    b64_cands = scan_b64_keys(data, iv16, ct)
    print(f"  Found {len(b64_cands)} unique b64-decodable candidates (16/24/32B)")
    for key_bytes in b64_cands:
        if check_key(key_bytes, iv16, ct):
            print(f"\n*** FOUND KEY (b64 source) ***")
            print(f"  Key hex: {key_bytes.hex()}")
            print(f"  Key bytes: {key_bytes!r}")
            break
    else:
        print(f"  Not found in b64 scan")

    print("\n--- Hex-encoded key scan ---")
    hex_cands = scan_hex_keys(data, iv16, ct)
    print(f"  Found {len(hex_cands)} unique hex-decodable candidates (16/24/32B)")
    for key_bytes in hex_cands:
        if check_key(key_bytes, iv16, ct):
            print(f"\n*** FOUND KEY (hex source) ***")
            print(f"  Key hex: {key_bytes.hex()}")
            print(f"  Key bytes: {key_bytes!r}")
            break
    else:
        print(f"  Not found in hex scan")

    print(f"\nTotal time: {time.time()-t0:.1f}s")
