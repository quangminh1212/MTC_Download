#!/usr/bin/env python3
"""Extract Dart snapshot from libapp.so"""
import struct
from pathlib import Path

def find_snapshot_offset(libapp_path):
    """Tìm offset của Dart snapshot trong libapp.so"""
    print(f"Analyzing: {libapp_path}")
    print("=" * 60)
    
    with open(libapp_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data):,} bytes")
    
    # Tìm magic bytes của Dart snapshot
    # Dart snapshot thường bắt đầu với: 0xf5, 0xf5, 0xdc, 0xdc
    magics = [
        (b'\xf5\xf5\xdc\xdc', "Dart 2.x snapshot"),
        (b'\xdc\xdc\xf5\xf5', "Dart 2.x snapshot (reversed)"),
        (b'\x00\x00\x00\xee', "Dart AOT snapshot"),
    ]
    
    for magic, desc in magics:
        offset = data.find(magic)
        if offset != -1:
            print(f"\n✅ Found {desc}")
            print(f"   Offset: 0x{offset:x} ({offset:,} bytes)")
            return offset, desc
    
    print("\n❌ Dart snapshot magic not found")
    print("\nTrying alternative method...")
    
    # Tìm section .rodata (thường chứa snapshot)
    rodata_marker = b'.rodata'
    offset = data.find(rodata_marker)
    if offset != -1:
        print(f"✅ Found .rodata section at: 0x{offset:x}")
        return offset, ".rodata section"
    
    return None, None

def extract_snapshot(libapp_path, output_path):
    """Extract snapshot từ libapp.so"""
    offset, desc = find_snapshot_offset(libapp_path)
    if not offset:
        return False
    
    with open(libapp_path, 'rb') as f:
        f.seek(offset)
        snapshot_data = f.read()
    
    with open(output_path, 'wb') as f:
        f.write(snapshot_data)
    
    print(f"\n✅ Snapshot extracted to: {output_path}")
    print(f"   Size: {len(snapshot_data):,} bytes")
    print(f"   Type: {desc}")
    
    # Analyze snapshot
    print(f"\n{'='*60}")
    print("Snapshot Analysis:")
    print('='*60)
    
    # Count printable strings
    strings = extract_strings(snapshot_data, min_length=20)
    print(f"Found {len(strings)} strings (length >= 20)")
    
    # Look for potential keys
    potential_keys = [s for s in strings if is_potential_key(s)]
    if potential_keys:
        print(f"\n✅ Found {len(potential_keys)} potential encryption keys:")
        for key in potential_keys[:10]:  # Show first 10
            print(f"   {key[:80]}...")
    else:
        print("\n⚠️  No obvious encryption keys found in strings")
    
    return True

def extract_strings(data, min_length=10):
    """Extract printable strings from binary data."""
    import re
    pattern = rb'[\x20-\x7E]{' + str(min_length).encode() + rb',}'
    strings = re.findall(pattern, data)
    return [s.decode('ascii', errors='ignore') for s in strings]

def is_potential_key(s):
    """Kiểm tra xem string có phải là key không."""
    import re
    
    # Base64 key (40-50 chars)
    if re.match(r'^[A-Za-z0-9+/]{40,50}={0,2}$', s):
        return True
    
    # Laravel key format
    if s.startswith('base64:') and len(s) > 50:
        return True
    
    # Hex key (64 chars for 256-bit)
    if re.match(r'^[0-9a-fA-F]{64}$', s):
        return True
    
    return False

def main():
    libapp = Path("extract/lib/arm64-v8a/libapp.so")
    output = Path("dart_snapshot.bin")
    
    if not libapp.exists():
        print(f"❌ File not found: {libapp}")
        print("\nMake sure you have extracted the APK first:")
        print("  1. Rename MTC.apk to MTC.zip")
        print("  2. Extract to 'extract' folder")
        return
    
    print("Dart Snapshot Extractor")
    print("=" * 60)
    
    if extract_snapshot(libapp, output):
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Use reFlutter to decompile:")
        print("     python reFlutter/reflutter.py MTC.apk")
        print("\n  2. Or analyze snapshot manually:")
        print("     python analyze_dart_snapshot.py")
        print("\n  3. Or use Ghidra to analyze libapp.so")
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print("\nTry alternative methods:")
        print("  1. Use reFlutter directly on APK")
        print("  2. Use mitmproxy to capture traffic")
        print("  3. Use Frida to hook decrypt functions")

if __name__ == "__main__":
    main()
