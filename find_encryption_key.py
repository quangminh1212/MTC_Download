#!/usr/bin/env python3
"""Find encryption key in APK files."""
import re
from pathlib import Path

# Search patterns for Laravel encryption key
patterns = [
    rb'APP_KEY=([A-Za-z0-9+/=]+)',
    rb'base64:([A-Za-z0-9+/=]{40,})',
    rb'"key"\s*:\s*"([^"]+)"',
    rb'encryption.*key.*["\']([A-Za-z0-9+/=]{40,})["\']',
]

def search_in_file(file_path, patterns):
    """Search for patterns in a file."""
    try:
        content = file_path.read_bytes()
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches
    except:
        pass
    return []

# Search in extract folder
extract_dir = Path("extract")
print("Searching for encryption key in extract folder...")
print("=" * 60)

found_keys = set()

# Search in common locations
search_paths = [
    extract_dir / "assets",
    extract_dir / "res",
    extract_dir,
]

for search_path in search_paths:
    if not search_path.exists():
        continue
    
    print(f"\nSearching in: {search_path}")
    
    for file_path in search_path.rglob("*"):
        if file_path.is_file() and file_path.stat().st_size < 10 * 1024 * 1024:  # Skip large files
            matches = search_in_file(file_path, patterns)
            if matches:
                print(f"  ✅ Found in: {file_path.relative_to(extract_dir)}")
                for match in matches:
                    key = match.decode('utf-8', errors='ignore')
                    found_keys.add(key)
                    print(f"     Key: {key}")

if found_keys:
    print(f"\n{'=' * 60}")
    print(f"Found {len(found_keys)} unique key(s):")
    for key in found_keys:
        print(f"  {key}")
else:
    print("\n❌ No encryption key found")
    print("\nTrying to search in specific files...")
    
    # Try specific files
    specific_files = [
        "assets/flutter_assets/AssetManifest.json",
        "assets/flutter_assets/.env",
        "res/values/strings.xml",
    ]
    
    for file_name in specific_files:
        file_path = extract_dir / file_name
        if file_path.exists():
            print(f"\nChecking: {file_name}")
            content = file_path.read_text(errors='ignore')
            print(content[:500])
