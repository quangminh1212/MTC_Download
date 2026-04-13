import zipfile, re, base64, sys

with zipfile.ZipFile('base.apk') as z:
    lib = z.read('lib/arm64-v8a/libapp.so')

print(f'lib size: {len(lib)}', flush=True)

# Search for AES-related strings and nearby context
for pattern in [b'{"iv":', b'"value":', b'AesCrypt', b'AESEngine', b'secretKey', b'encryptKey', b'_encryptKey', b'decryptKey']:
    pos = lib.find(pattern)
    if pos != -1:
        chunk = lib[max(0,pos-30):pos+80]
        print(f'FOUND {pattern}: offset {pos:#010x}')
        print(f'  ctx: {repr(chunk)}')
    else:
        print(f'NOT FOUND: {pattern}')

print()
# Also check for these patterns but with alternate forms
for pattern in [b'Encrypt', b'Decrypt', b'AES', b'aes', b'encrypt', b'decrypt']:
    positions = []
    pos = 0
    while True:
        idx = lib.find(pattern, pos)
        if idx == -1 or len(positions) > 5:
            break
        positions.append(idx)
        pos = idx + 1
    if positions:
        print(f'{pattern}: found at {positions}')
        # Show context for first occurrence
        idx = positions[0]
        print(f'  first ctx: {repr(lib[max(0,idx-10):idx+50])}')

print()
# Look for base64 strings of specific lengths (potential AES keys)
# AES-128: 16 bytes = 24 chars base64
# AES-256: 32 bytes = 44 chars base64
print('Searching for potential base64 keys...')

# Find all base64-looking strings of key lengths
b64_24 = re.findall(rb'[A-Za-z0-9+/]{22}==', lib)
b64_44 = re.findall(rb'[A-Za-z0-9+/]{43}=', lib)

print(f'24-char base64 (16-byte key) candidates: {len(b64_24)}')
for k in b64_24[:20]:
    try:
        decoded = base64.b64decode(k)
        # Check entropy (not all same byte, not sequential)
        entropy = len(set(decoded)) 
        if entropy > 8:
            print(f'  KEY?: {k.decode()} -> {decoded.hex()} (entropy={entropy})')
    except:
        pass

print(f'44-char base64 (32-byte key) candidates: {len(b64_44)}')
for k in b64_44[:20]:
    try:
        decoded = base64.b64decode(k)
        entropy = len(set(decoded))
        if entropy > 8:
            print(f'  KEY?: {k.decode()} -> {decoded.hex()} (entropy={entropy})')
    except:
        pass

print()
# Look for hex-encoded possible keys
hex_32 = list(set(re.findall(rb'[0-9a-fA-F]{32}', lib)))
print(f'32-char hex strings (16-byte key): {len(hex_32)}')
for k in hex_32[:10]:
    try:
        decoded = bytes.fromhex(k.decode())
        entropy = len(set(decoded))
        if entropy > 8:
            print(f'  KEY?: {k.decode()}')
    except:
        pass

hex_64 = list(set(re.findall(rb'[0-9a-fA-F]{64}', lib)))
print(f'64-char hex strings (32-byte key): {len(hex_64)}')
for k in hex_64[:10]:
    print(f'  {k.decode()}')
