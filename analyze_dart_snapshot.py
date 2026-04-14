#!/usr/bin/env python3
"""Analyze Dart snapshot để tìm encryption keys và strings."""
import re
from pathlib import Path
from collections import Counter

def extract_strings(data, min_length=10):
    """Extract printable ASCII strings."""
    pattern = rb'[\x20-\x7E]{' + str(min_length).encode() + rb',}'
    strings = re.findall(pattern, data)
    return [s.decode('ascii', errors='ignore') for s in strings]

def is_base64_key(s):
    """Check if string looks like a base64 key."""
    if re.match(r'^[A-Za-z0-9+/]{40,50}={0,2}$', s):
        return True
    if s.startswith('base64:') and len(s) > 50:
        return True
    return False

def is_hex_key(s):
    """Check if string looks like a hex key."""
    return re.match(r'^[0-9a-fA-F]{64}$', s) is not None

def find_encryption_patterns(strings):
    """Tìm các pattern liên quan đến encryption."""
    patterns = {
        'keys': [],
        'encryption_related': [],
        'api_related': [],
        'config_related': []
    }
    
    keywords = {
        'encryption': ['encrypt', 'decrypt', 'cipher', 'aes', 'key', 'iv'],
        'api': ['api', 'http', 'request', 'response', 'token'],
        'config': ['config', 'setting', 'env', 'app_key']
    }
    
    for s in strings:
        s_lower = s.lower()
        
        # Check for keys
        if is_base64_key(s) or is_hex_key(s):
            patterns['keys'].append(s)
            continue
        
        # Check for encryption-related
        if any(kw in s_lower for kw in keywords['encryption']):
            patterns['encryption_related'].append(s)
        
        # Check for API-related
        if any(kw in s_lower for kw in keywords['api']):
            patterns['api_related'].append(s)
        
        # Check for config-related
        if any(kw in s_lower for kw in keywords['config']):
            patterns['config_related'].append(s)
    
    return patterns

def analyze_snapshot(snapshot_path):
    """Phân tích Dart snapshot."""
    print(f"Analyzing: {snapshot_path}")
    print("=" * 60)
    
    with open(snapshot_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data):,} bytes")
    
    # Extract strings
    print("\nExtracting strings...")
    strings = extract_strings(data, min_length=15)
    print(f"Found {len(strings)} strings (length >= 15)")
    
    # Find patterns
    print("\nSearching for encryption patterns...")
    patterns = find_encryption_patterns(strings)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    # Potential keys
    if patterns['keys']:
        print(f"\n✅ Found {len(patterns['keys'])} potential encryption keys:")
        print("-" * 60)
        for key in patterns['keys'][:20]:  # Show first 20
            print(f"  {key}")
    else:
        print("\n❌ No obvious encryption keys found")
    
    # Encryption-related strings
    if patterns['encryption_related']:
        print(f"\n📝 Found {len(patterns['encryption_related'])} encryption-related strings:")
        print("-" * 60)
        for s in patterns['encryption_related'][:20]:
            print(f"  {s[:80]}")
    
    # API-related strings
    if patterns['api_related']:
        print(f"\n🌐 Found {len(patterns['api_related'])} API-related strings:")
        print("-" * 60)
        for s in patterns['api_related'][:20]:
            print(f"  {s[:80]}")
    
    # Config-related strings
    if patterns['config_related']:
        print(f"\n⚙️  Found {len(patterns['config_related'])} config-related strings:")
        print("-" * 60)
        for s in patterns['config_related'][:20]:
            print(f"  {s[:80]}")
    
    # Save all strings to file
    output_file = Path("dart_snapshot_strings.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(strings))
    
    print(f"\n✅ All strings saved to: {output_file}")
    
    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"Total strings: {len(strings)}")
    print(f"Potential keys: {len(patterns['keys'])}")
    print(f"Encryption-related: {len(patterns['encryption_related'])}")
    print(f"API-related: {len(patterns['api_related'])}")
    print(f"Config-related: {len(patterns['config_related'])}")

def main():
    snapshot = Path("dart_snapshot.bin")
    
    if not snapshot.exists():
        print(f"❌ File not found: {snapshot}")
        print("\nRun extract_dart_snapshot.py first:")
        print("  python extract_dart_snapshot.py")
        return
    
    print("Dart Snapshot Analyzer")
    print("=" * 60)
    
    analyze_snapshot(snapshot)
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\nIf keys found:")
    print("  1. Try each key with test_decrypt.py")
    print("  2. Test with Laravel decryption")
    print("\nIf no keys found:")
    print("  1. Use reFlutter to decompile full APK")
    print("  2. Use mitmproxy to capture network traffic")
    print("  3. Use Frida to hook decrypt functions")

if __name__ == "__main__":
    main()
