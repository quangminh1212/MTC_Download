import zipfile, re, base64, sys

print("Loading libapp.so...", flush=True)
with zipfile.ZipFile('base.apk') as z:
    lib = z.read('lib/arm64-v8a/libapp.so')
print(f'lib size: {len(lib)}', flush=True)

# 1. Quick exact pattern search
for pattern in [b'{"iv":', b'AesCrypt', b'AESEngine', b'secretKey', b'encryptKey']:
    pos = lib.find(pattern)
    if pos != -1:
        print(f'FOUND {pattern!r} at {pos:#010x}: {repr(lib[max(0,pos-30):pos+80])}')
    else:
        print(f'NOT: {pattern!r}')
sys.stdout.flush()

# 2. Find high-entropy 32-byte blocks (AES-256 keys are random-looking)
print("\nSearching 32-byte high-entropy blocks in .rodata...", flush=True)
# Only scan readable sections - find .rodata offset
# Simple: scan the first 5MB for sequences of printable chars that look like keys
# Look for what's immediately after AES-related strings in lib
aes_pos = lib.find(b'AesCrypt')
if aes_pos == -1:
    aes_pos = lib.find(b'AESEngine')
if aes_pos != -1:
    print(f"AES string at {aes_pos:#010x}")
    # Show 2KB around it
    chunk = lib[max(0, aes_pos-200):aes_pos+500]
    # Extract ASCII strings from this chunk
    strings = re.findall(rb'[\x20-\x7e]{4,}', chunk)
    for s in strings:
        print(f'  {s!r}')
sys.stdout.flush()

# 3. Search for base64 key candidates (faster using bytes)
print("\nLooking for 24-char base64 keys...", flush=True)
# Use a simple sliding window
b64chars = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
count = 0
seen = set()
for i in range(0, len(lib) - 24, 1):
    chunk = lib[i:i+24]
    if all(b in b64chars for b in chunk) and chunk.endswith(b'=='):
        # Does it decode to 16 bytes?
        try:
            decoded = base64.b64decode(chunk)
            if len(decoded) == 16 and len(set(decoded)) > 8 and chunk not in seen:
                seen.add(chunk)
                pos_ctx = lib[max(0,i-60):i+60]
                strings_near = re.findall(rb'[\x20-\x7e]{3,}', pos_ctx)
                print(f'  KEY? {chunk.decode()} = {decoded.hex()} near: {[s.decode() for s in strings_near[:5]]}')
                count += 1
                if count > 20:
                    break
        except:
            pass
print(f"Done. Found {count} candidates.")
