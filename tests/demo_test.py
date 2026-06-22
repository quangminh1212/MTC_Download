#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Test tải một truyện ngắn
"""

import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from mtc_downloader import MTCDownloader

def main():
    downloader = MTCDownloader()

    print("="*60)
    print("DEMO: Test tải truyện ngắn")
    print("="*60)

    # Tìm truyện ngắn (ít chương) để test
    print("\n🔍 Đang tìm truyện ngắn để test...")
    books = downloader.get_books(limit=50)

    if not books or "data" not in books:
        print("❌ Không thể lấy danh sách truyện")
        return

    # Lọc truyện có ít hơn 20 chương
    short_books = [b for b in books["data"] if b["chapter_count"] < 20]

    if not short_books:
        print("❌ Không tìm thấy truyện ngắn")
        return

    print(f"\n✅ Tìm thấy {len(short_books)} truyện ngắn:\n")

    for idx, book in enumerate(short_books[:5], 1):
        print(f"{idx}. {book['name']}")
        print(f"   ID: {book['id']}")
        print(f"   Số chương: {book['chapter_count']}")
        print()

    # Tải truyện ngắn nhất
    test_book = short_books[0]
    print(f"📥 Sẽ tải truyện: {test_book['name']}")
    print(f"   ID: {test_book['id']}")
    print(f"   Số chương: {test_book['chapter_count']}")

    print("\n" + "="*60)
    downloader.download_book(
        book_id=test_book['id'],
        output_dir="test_downloads",
        delay=0.3
    )

    print("\n✅ Demo hoàn tất!")
    print(f"📂 Kiểm tra thư mục: test_downloads/{downloader.sanitize_filename(test_book['name'])}")

if __name__ == "__main__":
    main()
