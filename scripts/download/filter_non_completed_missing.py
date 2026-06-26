#!/usr/bin/env python3
"""
Filter missing books to only non-completed (Còn tiếp + Tạm dừng)
"""
import json

MISSING_FILE = r"c:\Dev\MTC_Download\logs\local_repo_missing_books.json"
QUEUE_FILE = r"c:\Dev\MTC_Download\logs\non_completed_missing_queue.json"

def main():
    with open(MISSING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing_books = data['missing_books']
    
    # Filter to only non-completed (Còn tiếp + Tạm dừng)
    non_completed = [book for book in missing_books if book['status_name'] != 'Hoàn thành']
    
    # Extract just the IDs
    non_completed_ids = [book['id'] for book in non_completed]
    non_completed_ids.sort()
    
    print(f"Total missing books: {len(missing_books)}")
    print(f"Non-completed missing (Còn tiếp + Tạm dừng): {len(non_completed)}")
    
    # Break down by status
    by_status = {}
    for book in non_completed:
        status = book['status_name']
        by_status[status] = by_status.get(status, 0) + 1
    
    print(f"By status:")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")
    
    # Save queue
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(non_completed_ids, f, indent=2)
    
    print(f"\nQueue saved to: {QUEUE_FILE}")
    
    # Show sample
    if non_completed:
        print(f"\nSample (first 10):")
        for book in non_completed[:10]:
            print(f"  ID {book['id']}: {book['name']} ({book['status_name']}, {book['chapter_count']} chapters)")

if __name__ == '__main__':
    main()
