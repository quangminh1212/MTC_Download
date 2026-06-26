#!/usr/bin/env python3
"""
Scan local repository D:\Dev\MTC_Continune to find which books are missing.
Compare with the inventory to identify books that exist on server but not locally.
"""
import os
import json
from pathlib import Path
from collections import defaultdict

REPO = r"D:\Dev\MTC_Continune"
INVENTORY_FILE = r"c:\Dev\MTC_Download\logs\all_books_by_id_inventory.json"
OUTPUT_FILE = r"c:\Dev\MTC_Download\logs\local_repo_missing_books.json"

def scan_local_repo():
    """Scan local repo and return set of book IDs that exist locally."""
    local_ids = set()
    repo_path = Path(REPO)
    
    if not repo_path.exists():
        print(f"ERROR: Repo path does not exist: {REPO}")
        return local_ids
    
    print(f"Scanning local repo: {REPO}")
    
    # Each book is a directory named by its name (Vietnamese title)
    # We need to read info.json to get the book ID
    for item in repo_path.iterdir():
        if item.is_dir():
            info_file = item / "info.json"
            if info_file.exists():
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    book_id = info.get('id')
                    if book_id:
                        local_ids.add(book_id)
                except Exception as e:
                    print(f"Warning: Could not read {info_file}: {e}")
    
    print(f"Found {len(local_ids)} books in local repo")
    return local_ids

def load_inventory():
    """Load the inventory file."""
    print(f"Loading inventory: {INVENTORY_FILE}")
    with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Build a dict of ID -> book info for books that exist
    existing_books = {}
    for book in data.get('books', []):
        if book.get('exists'):
            existing_books[book['id']] = book
    
    print(f"Inventory has {len(existing_books)} existing books")
    return existing_books, data.get('stats', {})

def main():
    local_ids = scan_local_repo()
    existing_books, stats = load_inventory()
    
    # Find books that exist on server but not locally
    missing_ids = []
    missing_books = []
    
    for book_id, book_info in existing_books.items():
        if book_id not in local_ids:
            missing_ids.append(book_id)
            missing_books.append({
                'id': book_id,
                'name': book_info.get('name'),
                'status': book_info.get('status'),
                'status_name': book_info.get('status_name'),
                'chapter_count': book_info.get('chapter_count')
            })
    
    # Sort by ID
    missing_ids.sort()
    missing_books.sort(key=lambda x: x['id'])
    
    print(f"\n=== SUMMARY ===")
    print(f"Total existing books in inventory: {len(existing_books)}")
    print(f"Books in local repo: {len(local_ids)}")
    print(f"Missing from local repo: {len(missing_ids)}")
    
    # Break down by status
    by_status = defaultdict(int)
    for book in missing_books:
        by_status[book['status_name']] += 1
    
    print(f"\nMissing by status:")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")
    
    # Save results
    output = {
        'stats': {
            'total_existing': len(existing_books),
            'local_count': len(local_ids),
            'missing_count': len(missing_ids),
            'missing_by_status': dict(by_status)
        },
        'missing_ids': missing_ids,
        'missing_books': missing_books
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {OUTPUT_FILE}")
    
    # Show sample
    if missing_books:
        print(f"\nSample missing books (first 10):")
        for book in missing_books[:10]:
            print(f"  ID {book['id']}: {book['name']} ({book['status_name']}, {book['chapter_count']} chapters)")

if __name__ == '__main__':
    main()
