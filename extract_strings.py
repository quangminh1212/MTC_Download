#!/usr/bin/env python3
"""Extract strings from libapp.so to find encryption key."""
import re
from pathlib import Path

def extract_strings(file_path, min_length=10):
    """Extract printable strings from binary file."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Find ASCII strings
    pattern = rb'[\x20-\x7E]{' + str(min_length).encode() + rb',}'
    strings = re.findall(pattern, data)
    
    return [s.decode('ascii', errors='ignore') for s in strings]

libapp = Path("extract/lib/arm64-v8a/libapp.so")

print("Extracting strings from libapp.so...")
print("=" * 60)

strings = extract_strings(libapp, min_length=20)

# Filter for potential keys
keywords = ['key', 'secret', 'encrypt', 'APP_KEY', 'base64:', 'aes', 'cipher']

print(f"\nFound {len(strings)} strings (length >= 20)")
print("\nSearching for encryption-related strings...")
print("=" * 60)

found = []
for s in strings:
    s_lower = s.lower()
    if any(kw in s_lower for kw in keywords):
        found.append(s)
        print(f"\n{s}")

print(f"\n{'=' * 60}")
print(f"Found {len(found)} potential matches")

# Look for base64 encoded keys (typically 44 chars for 32-byte key)
print("\n" + "=" * 60)
print("Looking for base64-like strings (40-50 chars)...")
print("=" * 60)

base64_pattern = re.compile(r'^[A-Za-z0-9+/]{40,50}={0,2}$')
for s in strings:
    if base64_pattern.match(s):
        print(f"\n  {s}")

# Save all strings to file for manual inspection
output_file = Path("libapp_strings.txt")
output_file.write_text('\n'.join(strings), encoding='utf-8')
print(f"\n✅ All strings saved to: {output_file}")
