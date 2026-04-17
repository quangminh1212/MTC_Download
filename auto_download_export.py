#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Download & Export - Tải và xuất truyện tự động
"""

import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from pathlib import Path
from mtc_downloader import MTCDownloader
from mtc_exporter import MTCExporter


class AutoDownloadExport:
    """Tải và xuất truyện tự động"""

    def __init__(self, output_dir="downloads", delay=0.5):
        self.downloader = MTCDownloader()
        self.output_dir = output_dir
        self.delay = delay

    def process_book(self, book_id: int, export_formats: list = ['txt', 'html', 'md']):
        """Tải và xuất một truyện"""
        print(f"\n{'='*70}")
        print(f"🚀 Xử lý truyện ID: {book_id}")
        print(f"{'='*70}")

        # Bước 1: Tải truyện
        print("\n📥 BƯỚC 1: Tải truyện")
        success = self.downloader.download_book(book_id, self.output_dir, self.delay)

        if not success:
            print("❌ Tải truyện thất bại")
            return False

        # Bước 2: Tìm thư mục truyện
        book_info = self.downloader.get_book_detail(book_id)
        if not book_info or "data" not in book_info:
            print("❌ Không lấy được thông tin truyện")
            return False

        book_name = book_info["data"].get("name", f"book_{book_id}")
        book_dir = Path(self.output_dir) / self.downloader.sanitize_filename(book_name)

        if not book_dir.exists():
            print(f"❌ Không tìm thấy thư mục: {book_dir}")
            return False

        # Bước 3: Xuất file
        print("\n📦 BƯỚC 2: Xuất file")
        exporter = MTCExporter(book_dir)

        export_map = {
            'txt': exporter.export_txt,
            'html': exporter.export_html,
            'md': exporter.export_markdown,
        }

        for fmt in export_formats:
            if fmt in export_map:
                try:
                    export_map[fmt]()
                except Exception as e:
                    print(f"❌ Lỗi xuất {fmt.upper()}: {e}")

        print(f"\n✅ Hoàn thành xử lý truyện: {book_name}")
        return True

    def process_multiple(self, book_ids: list, export_formats: list = ['txt', 'html']):
        """Tải và xuất nhiều truyện"""
        print(f"\n{'='*70}")
        print(f"🚀 Xử lý {len(book_ids)} truyện")
        print(f"{'='*70}")

        results = []
        for idx, book_id in enumerate(book_ids, 1):
            print(f"\n[{idx}/{len(book_ids)}] Đang xử lý truyện ID: {book_id}")
            success = self.process_book(book_id, export_formats)
            results.append((book_id, success))

        # Tổng kết
        print(f"\n{'='*70}")
        print("📊 KẾT QUẢ TỔNG HỢP")
        print(f"{'='*70}")

        success_count = sum(1 for _, s in results if s)
        print(f"✅ Thành công: {success_count}/{len(book_ids)}")

        if success_count < len(book_ids):
            print(f"❌ Thất bại: {len(book_ids) - success_count}")
            print("\nDanh sách thất bại:")
            for book_id, success in results:
                if not success:
                    print(f"  - ID: {book_id}")

        print(f"{'='*70}\n")


def main():
    """Demo"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     AUTO DOWNLOAD & EXPORT - Tải và xuất tự động            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Cấu hình
    processor = AutoDownloadExport(output_dir="downloads", delay=0.5)

    # Lấy danh sách truyện mới
    print("📚 Đang lấy danh sách truyện mới...")
    books = processor.downloader.get_books(limit=10)

    if not books or "data" not in books:
        print("❌ Không thể lấy danh sách truyện")
        return

    print(f"\n✅ Tìm thấy {len(books['data'])} truyện:\n")
    print(f"{'STT':<5} {'ID':<8} {'Tên truyện':<45} {'Chương':>8}")
    print("-" * 70)

    for idx, book in enumerate(books["data"], 1):
        name = book.get("name", "Unknown")[:43]
        chapters = book.get("chapter_count") or book.get("latest_index", 0)
        book_id = book.get("id", 0)
        print(f"{idx:<5} {book_id:<8} {name:<45} {chapters:>8}")

    # Chọn truyện
    print("\n" + "="*70)
    choice = input("Nhập số thứ tự truyện muốn tải (hoặc Enter để tải 3 truyện đầu): ").strip()

    if choice:
        try:
            idx = int(choice)
            if 1 <= idx <= len(books["data"]):
                book_id = books["data"][idx-1]["id"]
                processor.process_book(book_id, export_formats=['txt', 'html', 'md'])
            else:
                print("❌ Số thứ tự không hợp lệ")
        except ValueError:
            print("❌ Lựa chọn không hợp lệ")
    else:
        # Tải 3 truyện đầu
        book_ids = [book["id"] for book in books["data"][:3]]
        processor.process_multiple(book_ids, export_formats=['txt', 'html'])

    print("\n✅ Hoàn tất!")


if __name__ == "__main__":
    main()
