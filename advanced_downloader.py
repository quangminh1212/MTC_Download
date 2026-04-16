#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Advanced Downloader - Tải truyện với progress bar và export TXT
"""

import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import json
import time
from pathlib import Path
from mtc_downloader import MTCDownloader

class AdvancedDownloader(MTCDownloader):
    """Extended downloader với thêm tính năng"""

    def export_to_txt(self, book_dir: Path, output_file: str = None):
        """Xuất tất cả chương sang file TXT"""
        if not output_file:
            output_file = book_dir / "full_book.txt"
        else:
            output_file = Path(output_file)

        print(f"\n📝 Đang xuất sang TXT: {output_file.name}")

        # Đọc info
        info_file = book_dir / "info.json"
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
                book_name = info.get('name', 'Unknown')
                author = info.get('author', 'Unknown')
                synopsis = info.get('synopsis', '')
        else:
            book_name = book_dir.name
            author = 'Unknown'
            synopsis = ''

        # Lấy tất cả file chương
        chapter_files = sorted(book_dir.glob("chapter_*.json"))

        if not chapter_files:
            print("❌ Không tìm thấy chương nào")
            return False

        # Ghi file TXT
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("="*60 + "\n")
            f.write(f"{book_name}\n")
            f.write("="*60 + "\n\n")
            f.write(f"Tác giả: {author}\n\n")

            if synopsis:
                f.write("Tóm tắt:\n")
                f.write(synopsis + "\n\n")

            f.write("="*60 + "\n\n")

            # Nội dung các chương
            for idx, chapter_file in enumerate(chapter_files, 1):
                try:
                    with open(chapter_file, 'r', encoding='utf-8') as cf:
                        chapter_data = json.load(cf)
                        chapter_name = chapter_data.get('name', f'Chương {idx}')
                        content = chapter_data.get('content', '')

                        # Ghi chương
                        f.write(f"\n{'='*60}\n")
                        f.write(f"{chapter_name}\n")
                        f.write(f"{'='*60}\n\n")
                        f.write(content)
                        f.write("\n\n")

                        print(f"  [{idx}/{len(chapter_files)}] ✅ {chapter_name}")

                except Exception as e:
                    print(f"  [{idx}/{len(chapter_files)}] ❌ Lỗi: {e}")

        print(f"\n✅ Đã xuất {len(chapter_files)} chương sang: {output_file}")
        return True

    def download_and_export(self, book_id: int, output_dir="downloads", export_txt=True):
        """Tải truyện và tự động export sang TXT"""
        print(f"\n{'='*60}")
        print(f"📚 Tải và xuất truyện ID: {book_id}")
        print(f"{'='*60}")

        # Tải truyện
        success = self.download_book(book_id, output_dir, delay=0.5)

        if not success:
            print("❌ Tải truyện thất bại")
            return False

        if export_txt:
            # Tìm thư mục truyện vừa tải
            book_info = self.get_book_detail(book_id)
            if book_info and "data" in book_info:
                book_name = book_info["data"].get("name", f"book_{book_id}")
                book_dir = Path(output_dir) / self.sanitize_filename(book_name)

                if book_dir.exists():
                    self.export_to_txt(book_dir)

        return True

    def show_progress(self, current: int, total: int, prefix: str = ""):
        """Hiển thị progress bar đơn giản"""
        percent = int(current * 100 / total)
        bar_length = 40
        filled = int(bar_length * current / total)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(f"\r{prefix} [{bar}] {percent}% ({current}/{total})", end="", flush=True)

        if current == total:
            print()  # Newline khi hoàn thành


def main():
    downloader = AdvancedDownloader()

    print("="*60)
    print("MTC ADVANCED DOWNLOADER")
    print("Tải truyện + Export TXT tự động")
    print("="*60)

    # Lấy danh sách truyện
    print("\n📚 Đang lấy danh sách truyện...")
    books = downloader.get_books(limit=10)

    if not books or "data" not in books:
        print("❌ Không thể lấy danh sách truyện")
        return

    print(f"\n✅ Tìm thấy {len(books['data'])} truyện:\n")

    for idx, book in enumerate(books["data"], 1):
        print(f"{idx:2d}. [{book['id']:6d}] {book['name'][:45]:45s} - {book['chapter_count']:4d} chương")

    # Ví dụ: Tải truyện đầu tiên
    print("\n" + "="*60)
    print("📥 Demo: Tải truyện đầu tiên và export TXT")
    print("="*60)

    first_book_id = books["data"][0]["id"]
    downloader.download_and_export(
        book_id=first_book_id,
        output_dir="downloads",
        export_txt=True
    )

    print("\n✅ Hoàn tất!")


if __name__ == "__main__":
    main()
