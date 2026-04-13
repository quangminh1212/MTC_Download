"""Search libapp.so for plain UTF-8 AES key strings (16 or 32 chars)."""
import zipfile, re, sys, zlib
sys.stdout.reconfigure(encoding='utf-8')

print("Loading libapp.so...", flush=True)
with zipfile.ZipFile('base.apk') as z:
    lib = z.read('lib/arm64-v8a/libapp.so')
    # Also check NOTICES for package list
    try:
        notices_z = z.read('assets/flutter_assets/NOTICES.Z')
        notices = zlib.decompress(notices_z).decode('utf-8', errors='replace')
        # Find encryption-related package mentions
        lines = notices.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ['encrypt', 'aes', 'crypt', 'cipher', 'crypto']):
                print(f"NOTICE: {line}")
    except Exception as e:
        print(f"NOTICES error: {e}")

print("\nSearching for 16/32-char ASCII strings...", flush=True)

# Extract ALL ASCII strings of length 16 or 32 from libapp.so (potential keys)
# These are the most likely candidates for Key.fromUtf8()
seen_16 = set()
seen_32 = set()
for m in re.finditer(rb'[\x20-\x7e]{16,64}', lib):
    s = m.group()
    pos = m.start()
    # Check exact length 16 strings
    for start in range(len(s) - 16 + 1):
        candidate_16 = s[start:start+16]
        if len(candidate_16) == 16 and candidate_16 not in seen_16:
            # Must look like a key: mixed chars, not all alpha, not a URL piece
            text = candidate_16.decode('ascii')
            if not candidate_16.isalpha() and not candidate_16.isdigit():
                if not any(prefix in text for prefix in ['http', 'com.', 'net.', 'flutter', 'android']):
                    seen_16.add(candidate_16)
    # Check exact length 32 strings
    for start in range(len(s) - 32 + 1):
        candidate_32 = s[start:start+32]
        if len(candidate_32) == 32 and candidate_32 not in seen_32:
            text = candidate_32.decode('ascii')
            if not candidate_32.isalpha():
                if not any(prefix in text for prefix in ['http', '.com', '.net', 'flutter', 'android']):
                    seen_32.add(candidate_32)

print(f"Found {len(seen_16)} 16-char mixed candidates")
print(f"Found {len(seen_32)} 32-char mixed candidates")

# Filter for high-entropy candidates (avoid sequential or repetitive strings)  
def entropy_score(s):
    return len(set(s.lower()))

high16 = sorted([s for s in seen_16 if entropy_score(s) >= 8], key=lambda s: -entropy_score(s))
high32 = sorted([s for s in seen_32 if entropy_score(s) >= 12], key=lambda s: -entropy_score(s))

print(f"\nHigh-entropy 16-char keys ({len(high16)}):")
for s in high16[:30]:
    print(f'  {s.decode("ascii")!r} (entropy={entropy_score(s)})')

print(f"\nHigh-entropy 32-char keys ({len(high32)}):")
for s in high32[:30]:
    print(f'  {s.decode("ascii")!r} (entropy={entropy_score(s)})')
