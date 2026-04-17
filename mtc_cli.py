#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC CLI - Giao diện dòng lệnh tương tác để tải truyện
"""

import sys
import time
from mtc_downloader import MTCDownloader

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class MTCCLI:
    def __init__(self):
        self.downloader = MTCDownloader()
        self.output_dir = "downloads"
        self.delay = 0.5

    def print_banner(self):
        print("""
╔══════════════════════════════════════════════════════╗
║            MTC DOWNLOADER - Tải Truyện              ║
╠══════════════════════════════════════════════════════╣
║ 1. Tìm kiếm truyện                                  ║
║ 2. Xem truyện mới                                   ║
║ 3. Tải truyện theo ID                               ║
║ 4. Tải nhiều truyện                                 ║
║ 0. Thoát                                            ║
╚══════════════════════════════════════════════════════╝
""")

    def search_books(self, query: str):
        print(f"\n🔍 Đang tìm: {query}")
        results = []
        for page in range(1, 5):
            books = self.downloader.get_books(limit=20, page=page)
            if not books or "data" not in books:
                break
            for book in books["data"]:
                if query.lower() in book.get("name", "").lower():
                    results.append(book)
            time.sleep(self.delay)
        return results

    def get_new_books(self, limit: int = 20):
        print(f"\n📚 Đang lấy {limit} truyện mới nhất...")
        books = self.downloader.get_books(limit=limit)
        if books and "data" in books:
            return books["data"]
        return []

    def display_books(self, books):
        if not books:
            print("❌ Không tìm thấy truyện nào")
            return
        print(f"\n{'─' * 90}")
        print(f"{'STT':<5} {'Tên truyện':<55} {'Chương':>10} {'ID':>12}")
        print(f"{'─' * 90}")
        for idx, book in enumerate(books, 1):
            name = book.get("name", "Unknown")[:53]
            chapters = book.get("chapter_count") or book.get("latest_index", 0)
            book_id = book.get("id", 0)
            print(f"{idx:<5} {name:<55} {chapters:>10} {book_id:>12}")
        print(f"{'─' * 90}")

    def select_books(self, books):
        choice = input("\nNhập STT cần tải (vd 1,3,5 hoặc 1-3): ").strip()
        selected_ids = []
        try:
            if '-' in choice and ',' not in choice:
                start, end = choice.split('-')
                for i in range(int(start), int(end) + 1):
                    if 1 <= i <= len(books):
                        selected_ids.append(books[i - 1]["id"])
            else:
                for part in choice.split(','):
                    part = part.strip()
                    if not part:
                        continue
                    idx = int(part)
                    if 1 <= idx <= len(books):
                        selected_ids.append(books[idx - 1]["id"])
        except ValueError:
            print("❌ Lựa chọn không hợp lệ")
        return selected_ids

    def download_selected_books(self, book_ids):
        if not book_ids:
            print("❌ Chưa chọn truyện nào")
            return
        print(f"\n🚀 Bắt đầu tải {len(book_ids)} truyện")
        self.downloader.download_multiple_books(book_ids, self.output_dir, self.delay)

    def download_by_id(self):
        try:
            book_id = int(input("Nhập ID truyện: ").strip())
        except ValueError:
            print("❌ ID không hợp lệ")
            return
        self.downloader.download_book(book_id, self.output_dir, self.delay)

    def show_and_download(self, books):
        self.display_books(books)
        if not books:
            return
        book_ids = self.select_books(books)
        if book_ids:
            self.download_selected_books(book_ids)

    def run(self):
        while True:
            self.print_banner()
            choice = input("➜ Chọn: ").strip()
            if choice == '1':
                query = input("Nhập từ khóa tìm kiếm: ").strip()
                if query:
                    self.show_and_download(self.search_books(query))
            elif choice == '2':
                self.show_and_download(self.get_new_books(20))
            elif choice == '3':
                self.download_by_id()
            elif choice == '4':
                ids_str = input("Nhập các ID, cách nhau bằng dấu phẩy: ").strip()
                try:
                    book_ids = [int(x.strip()) for x in ids_str.split(',') if x.strip()]
                    self.download_selected_books(book_ids)
                except ValueError:
                    print("❌ ID không hợp lệ")
            elif choice == '0':
                print("👋 Tạm biệt!")
                break
            else:
                print("❌ Lựa chọn không hợp lệ")
            input("\nNhấn Enter để tiếp tục...")


def main():
    MTCCLI().run()


if __name__ == "__main__":
    main()
