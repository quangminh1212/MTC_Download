#!/usr/bin/env python3
"""
Download all missing books from local_repo_missing_books.json
"""
import json
import sys
from pathlib import Path

MISSING_FILE = r"c:\Dev\MTC_Download\logs\local_repo_missing_books.json"
QUEUE_FILE = r"c:\Dev\MTC_Download\logs\missing_books_queue.json"

def main():
    with open(MISSING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing_ids = data['missing_ids']
    
    print(f"Creating queue with {len(missing_ids)} book IDs")
    
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(missing_ids, f, indent=2)
    
    print(f"Queue saved to: {QUEUE_FILE}")

if __name__ == '__main__':
    main()
