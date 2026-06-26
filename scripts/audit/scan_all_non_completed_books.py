#!/usr/bin/env python3
"""
Scan a wide ID range to find all non-completed books (Còn tiếp + Tạm dừng)
"""
import json
import sys
from pathlib import Path

from mtc_downloader import MTCDownloader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_FILE = r"C:\Dev_MTC_Download\logs\all_non_completed_books.json"

def scan_range(downloader: MTCDownloader, start_id: int, end_id: int) -> list:
    """Scan a range of book IDs for non-completed books."""
    non_completed = []
    
    for book_id in range(start_id, end_id + 1):
        try:
            data = downloader.get_chapters(book_id, limit=1)
            if not data:
                continue
            
            extra = data.get("extra", {})
            book_info = extra.get("book", {})
            
            if not book_info:
                continue
            
            status = book_info.get("status")
            status_name = book_info.get("status_name", "")
            
            # status: 1 = Còn tiếp, 2 = Hoàn thành, 3 = Tạm dừng
            if status in [1, 3]:  # Non-completed
                non_completed.append({
                    "id": book_id,
                    "name": book_info.get("name", ""),
                    "status": status,
                    "status_name": status_name,
                    "chapter_count": book_info.get("latest_index", 0)
                })
                print(f"Found non-completed: ID {book_id} - {book_info.get('name')} ({status_name})")
        
        except Exception as e:
            # Book doesn't exist or error
            continue
    
    return non_completed

def main():
    downloader = MTCDownloader()
    
    # Scan in large chunks
    all_non_completed = []
    
    # Start from where we left off (153616) and go much higher
    # Let's scan up to 500000 to find more books
    ranges = [
        (153617, 200000),
        (200001, 250000),
        (250001, 300000),
        (300001, 350000),
        (350001, 400000),
        (400001, 450000),
        (450001, 500000),
    ]
    
    for start, end in ranges:
        print(f"\nScanning range {start}-{end}...")
        books = scan_range(downloader, start, end)
        all_non_completed.extend(books)
        print(f"Found {len(books)} non-completed books in this range")
        
        # Save progress
        output = {
            "total_found": len(all_non_completed),
            "books": all_non_completed
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total non-completed books found: {len(all_non_completed)}")
    
    # Break down by status
    by_status = {}
    for book in all_non_completed:
        status = book['status_name']
        by_status[status] = by_status.get(status, 0) + 1
    
    print(f"By status:")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")
    
    print(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
