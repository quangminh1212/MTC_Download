"""
Extract libapp.so from base.apk and run brute-force key search.
"""

import os, sys, zipfile, base64, requests, time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import urllib3
urllib3.disable_warnings()

APK_PATH = r"C:\Dev\MTC_Download\base.apk"
EXTRACT_DIR = r"C:\Dev\MTC_Download\libapp_extracted"
API = "https://android.lonoapp.net/api"
SESS = requests.Session()
SESS.verify = False
SESS.timeout = 15

# ---- Step 1: Extract libapp.so from APK ----
os.makedirs(EXTRACT_DIR, exist_ok=True)
libapp_path = os.path.join(EXTRACT_DIR, "libapp.so")

if not os.path.exists(libapp_path):
    print(f"Extracting libapp.so from {APK_PATH}...")
    with zipfile.ZipFile(APK_PATH) as z:
        # List .so files
        so_files = [n for n in z.namelist() if n.endswith('.so')]
        print(f"Found .so files: {so_files}")
        
        # Pick libapp.so (x86_64 preferred, then x86, then arm64-v8a)
        for arch in ['x86_64', 'x86', 'arm64-v8a', 'armeabi-v7a']:
            candidate = f"lib/{arch}/libapp.so"
            if candidate in so_files:
                print(f"Extracting {candidate}...")
                with z.open(candidate) as src:
                    with open(libapp_path, 'wb') as dst:
                        dst.write(src.read())
                print(f"Extracted to {libapp_path} ({os.path.getsize(libapp_path):,} bytes)")
                break
        else:
            # Try any libapp.so
            for name in so_files:
                if 'libapp.so' in name:
                    print(f"Extracting {name}...")
                    with z.open(name) as src:
                        with open(libapp_path, 'wb') as dst:
                            dst.write(src.read())
                    print(f"Done: {os.path.getsize(libapp_path):,} bytes")
                    break
else:
    print(f"libapp.so already exists ({os.path.getsize(libapp_path):,} bytes)")

# ---- Step 2: Fetch encrypted chapter ----
def fetch_chapter(ch_id):
    print(f"\nFetching chapter {ch_id}...")
    r = SESS.get(f"{API}/chapters/{ch_id}")
    r.raise_for_status()
    d = r.json()
    data = d.get("data", d)
    content = data.get("content") if isinstance(data, dict) else None
    if not content:
        raise ValueError(f"No content: {str(d)[:300]}")
    outer = base64.b64decode(content + "==")
    sep = b'","value":"'
    pos = outer.find(sep)
    if pos < 0:
        raise ValueError(f"No separator: {outer[:100]!r}")
    iv16 = outer[7:23]
    ct = base64.b64decode(outer[pos + 11:-2] + b"==")
    print(f"IV: {iv16.hex()}, CT len: {len(ct)}")
    return iv16, ct

iv, ct = fetch_chapter(21589884)

# ---- Step 3: Extract key candidates from libapp.so ----
print(f"\nReading libapp.so ({os.path.getsize(libapp_path):,} bytes)...")
with open(libapp_path, "rb") as f:
    data = f.read()

candidates = []
b64_chars = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')

# 1. Printable ASCII strings of exact length
for target in (16, 24, 32):
    seen = set()
    for i in range(len(data) - target):
        chunk = data[i:i + target]
        if all(32 <= b <= 126 for b in chunk) and chunk not in seen:
            seen.add(chunk)
            candidates.append(chunk)
    print(f"  ASCII len={target}: {len(seen):,} candidates (cumulative: {len(candidates):,})")

# 2. Base64-encoded keys that decode to 16/24/32 bytes
b64_seen = set()
for b64_len in (24, 32, 44, 48):  # b64 lengths for 16, 24, 32, 36 byte keys
    for i in range(len(data) - b64_len):
        chunk = data[i:i + b64_len]
        if all(b in b64_chars for b in chunk) and chunk not in b64_seen:
            b64_seen.add(chunk)
            try:
                decoded = base64.b64decode(chunk + b"==")
                if len(decoded) in (16, 24, 32):
                    candidates.append(decoded)
            except:
                pass

print(f"Total candidates (with base64 variants): {len(candidates):,}")

# ---- Step 4: Brute force ----
print(f"\nBrute-forcing {len(candidates):,} candidates...")
print("(This may take a while...)")

found = []
start = time.time()

for i, key_bytes in enumerate(candidates):
    if len(key_bytes) not in (16, 24, 32):
        continue
    
    if i % 50000 == 0 and i > 0:
        elapsed = time.time() - start
        rate = i / elapsed
        remaining = (len(candidates) - i) / rate
        print(f"  {i:,}/{len(candidates):,} @ {rate:.0f}/s  ETA: {remaining:.0f}s")
    
    try:
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        plain = unpad(cipher.decrypt(ct), 16)
        # Check if valid UTF-8
        text = plain.decode("utf-8")
        # Additional check: should contain Vietnamese-like text
        print(f"\n{'!'*70}")
        print(f"KEY FOUND at candidate {i}!")
        print(f"Key bytes (hex): {key_bytes.hex()}")
        print(f"Key (repr): {key_bytes!r}")
        print(f"Plaintext[:300]:\n{text[:300]}")
        print('!'*70)
        found.append((key_bytes, text))
    except Exception:
        pass

elapsed = time.time() - start
print(f"\nCompleted: {len(candidates):,} candidates in {elapsed:.1f}s ({len(candidates)/elapsed:.0f}/s)")

if found:
    print(f"\n{'='*70}")
    print(f"TOTAL KEYS FOUND: {len(found)}")
    for kb, text in found:
        print(f"\nKey hex: {kb.hex()}")
        print(f"Key repr: {kb!r}")
        print(f"Text: {text[:500]}")
else:
    print("\nNo key found in printable ASCII or base64 candidates.")
    print("Consider testing raw 16/32-byte binary sequences (much larger search space).")
