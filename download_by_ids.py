#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Download by IDs - Tải truyện theo danh sách ID
"""

import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from mtc_downloader import MTCDownloader

def main():
    # Danh sách ID truyện cần tải
    # Thay đổi danh sách này theo nhu cầu
    BOOK_IDS = [
        140101,  # Thiên Địa Lưu Tiên - 189 chương
        140643,  # Lãng Nhân: Mỹ Nữ, Mời Tư Vấn - 781 chương
        139039,  # Đấu La: Khí Vận Chi Nữ - 690 chương
    ]

    downloader = MTCDownloader()

    print("="*60)
    print("MTC DOWNLOAD BY IDs")
    print("="*60)
    print(f"\n📋 Danh sách {len(BOOK_IDS)} truyện cần tải:")

    for idx, book_id in enumerate(BOOK_IDS, 1):
        print(f"  {idx}. ID: {book_id}")

    print("\n" + "="*60)
    print("🚀 Bắt đầu tải...")
    print("="*60)

    downloader.download_multiple_books(
        book_ids=BOOK_IDS,
        output_dir="downloads",
        delay=0.5  # Delay giữa các request (giây)
    )

    print("\n✅ Hoàn tất tất cả!")

if __name__ == "__main__":
    main()
