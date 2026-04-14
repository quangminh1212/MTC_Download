#!/usr/bin/env python3
"""Find URLs in libapp_strings.txt"""
import re

try:
    with open('libapp_strings.txt', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find URLs
    urls = re.findall(r'https?://[a-zA-Z0-9.-]+(?:/[^\s]*)?', content)
    unique_urls = list(set(urls))
    
    print(f"Found {len(unique_urls)} unique URLs:")
    print("=" * 60)
    
    for url in sorted(unique_urls)[:30]:
        print(url)
        
except FileNotFoundError:
    print("libapp_strings.txt not found. Run extract_strings.py first.")
