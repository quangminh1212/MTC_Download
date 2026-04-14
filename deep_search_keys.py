#!/usr/bin/env python3
"""Tìm kiếm sâu hơn trong strings để tìm encryption keys."""
import re
from pathlib import Path

def search_for_keys():
    """Tìm kiếm các pattern có thể là encryption key."""
    
    strings_file = Path("libapp_strings.txt")
    if not strings_file.exists():
        print("❌ libapp_strings.txt not found")
        return
    
    with open(strings_file, 'r', encoding='utf-8', errors='ignore') as f:
        strings = f.readlines()
    
    print(f"Analyzing {len(strings)} strings...")
    print("=" * 60)
    
    # Các pattern để tìm
    patterns = {
        'base64_key': r'base64:[A-Za-z0-9+/]{40,}={0,2}',
        'long_base64': r'^[A-Za-z0-9+/]{40,60}={0,2}$',
        'hex_key': r'^[0-9a-fA-F]{64}$',
        'app_key': r'APP_KEY.*[=:].*[A-Za-z0-9+/]{20,}',
        'encryption_key': r'ENCRYPTION_KEY.*[=:].*[A-Za-z0-9+/]{20,}',
        'secret': r'SECRET.*[=:].*[A-Za-z0-9+/]{20,}',
    }
    
    results = {}
    
    for pattern_name, pattern in patterns.items():
        matches = []
        for line in strings:
            line = line.strip()
            if re.search(pattern, line, re.IGNORECASE):
                matches.append(line)
        
        if matches:
            results[pattern_name] = matches
    
    # Display results
    if results:
        print("\n✅ Found potential keys:")
        print("=" * 60)
        
        for pattern_name, matches in results.items():
            print(f"\n📝 Pattern: {pattern_name}")
            print(f"   Found: {len(matches)} matches")
            print("-" * 60)
            
            for match in matches[:10]:  # Show first 10
                print(f"   {match[:100]}")
    else:
        print("\n❌ No obvious keys found with standard patterns")
        print("\nTrying alternative search...")
        
        # Tìm các string dài có thể là key
        print("\n" + "=" * 60)
        print("Looking for long alphanumeric strings...")
        print("=" * 60)
        
        long_strings = []
        for line in strings:
            line = line.strip()
            # String dài 40-60 chars, chỉ chứa alphanumeric và +/=
            if 40 <= len(line) <= 60:
                if re.match(r'^[A-Za-z0-9+/=]+$', line):
                    long_strings.append(line)
        
        if long_strings:
            print(f"\n✅ Found {len(long_strings)} long alphanumeric strings:")
            print("-" * 60)
            for s in long_strings[:20]:
                print(f"   {s}")
        else:
            print("\n❌ No long alphanumeric strings found")

if __name__ == "__main__":
    search_for_keys()
