#!/usr/bin/env python3
"""Extract strings from libflutter.so"""
import re
from pathlib import Path

def extract_strings(file_path, min_length=20):
    """Extract printable strings from binary file."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Find ASCII strings
    pattern = rb'[\x20-\x7E]{' + str(min_length).encode() + rb',}'
    strings = re.findall(pattern, data)
    
    return [s.decode('ascii', errors='ignore') for s in strings]

libflutter = Path("extract/lib/arm64-v8a/libflutter.so")

print("Extracting strings from libflutter.so...")
print("=" * 60)

strings = extract_strings(libflutter, min_length=20)

print(f"\nFound {len(strings)} strings (length >= 20)")

# Look for encryption-related
keywords = ['key', 'secret', 'encrypt', 'decrypt', 'aes', 'cipher', 'base64']

print("\nSearching for encryption-related strings...")
print("=" * 60)

found = []
for s in strings:
    s_lower = s.lower()
    if any(kw in s_lower for kw in keywords):
        found.append(s)

if found:
    print(f"\n✅ Found {len(found)} encryption-related strings:")
    print("-" * 60)
    for s in found[:30]:
        print(f"   {s[:100]}")
else:
    print("\n❌ No encryption-related strings found")

# Look for base64-like strings
print("\n" + "=" * 60)
print("Looking for base64-like strings (40-60 chars)...")
print("=" * 60)

base64_pattern = re.compile(r'^[A-Za-z0-9+/]{40,60}={0,2}$')
base64_strings = [s for s in strings if base64_pattern.match(s)]

if base64_strings:
    print(f"\n✅ Found {len(base64_strings)} base64-like strings:")
    print("-" * 60)
    for s in base64_strings[:20]:
        print(f"   {s}")
else:
    print("\n❌ No base64-like strings found")

# Save all strings
output_file = Path("libflutter_strings.txt")
output_file.write_text('\n'.join(strings), encoding='utf-8')
print(f"\n✅ All strings saved to: {output_file}")
