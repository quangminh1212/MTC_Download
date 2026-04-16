#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Batch Downloader - Tải truyện hàng loạt tự động
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
    print("MTC BATCH DOWNLOADER")
    print("="*60)

    # Lấy danh sách truyện
    print("\n📚 Đang lấy danh sách truyện...")
    books = downloader.get_books(limit=20)

    if not books or "data" not in books:
        print("❌ Không thể lấy danh sách truyện")
        return

    print(f"\n✅ Tìm thấy {len(books['data'])} truyện\n")

    # Hiển thị danh sách
    for idx, book in enumerate(books["data"], 1):
        print(f"{idx:2d}. [{book['id']:6d}] {book['name'][:50]:50s} - {book['chapter_count']:4d} chương")

    # Tải 3 truyện đầu tiên làm ví dụ
    print("\n" + "="*60)
    print("📥 Bắt đầu tải 3 truyện đầu tiên...")
    print("="*60)

    book_ids = [book["id"] for book in books["data"][:3]]
    downloader.download_multiple_books(book_ids, output_dir="downloads", delay=0.5)

    print("\n✅ Hoàn tất!")

if __name__ == "__main__":
    main()
