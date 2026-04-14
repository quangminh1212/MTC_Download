#!/usr/bin/env python3
"""cli.py – Unified CLI for downloading novels via API.

Usage:
    python cli.py "Tên Truyện"         # download one book
    python cli.py --all                 # download all from catalog
    python cli.py --refresh             # refresh catalog then download all
    python cli.py --completed           # only completed books
    python cli.py --list                # list catalog
    python cli.py --search "keyword"    # search API
"""
import argparse
import sys
from pathlib import Path

from download.config import OUTPUT_DIR, log
from download.api import create_session, search_books
from download.downloader import (
    download_book,
    download_batch,
    load_catalog,
    refresh_catalog,
)
from download.utils import safe_name


def main():
    parser = argparse.ArgumentParser(description="MTC Novel Downloader (API)")
    parser.add_argument("book", nargs="?", help="Tên truyện cần tải")
    parser.add_argument("--all", action="store_true", help="Tải tất cả từ catalog")
    parser.add_argument("--refresh", action="store_true", help="Cập nhật catalog từ API rồi tải")
    parser.add_argument("--completed", action="store_true", help="Chỉ tải truyện hoàn thành")
    parser.add_argument("--list", action="store_true", help="Liệt kê catalog")
    parser.add_argument("--search", help="Tìm kiếm truyện trên API")
    parser.add_argument("--start", type=int, default=1, help="Chương bắt đầu (mặc định 1)")
    parser.add_argument("--end", type=int, help="Chương kết thúc (mặc định: hết)")
    parser.add_argument("--id", type=int, help="Book ID (chính xác)")
    parser.add_argument("--limit", type=int, help="Giới hạn số truyện khi --all")
    parser.add_argument("--no-skip", action="store_true", help="Không bỏ qua truyện đã tải đủ")
    parser.add_argument("-o", "--output", type=str, help="Thư mục output")
    args = parser.parse_args()

    output = Path(args.output) if args.output else OUTPUT_DIR

    # --- List catalog ---
    if args.list:
        books = load_catalog()
        if not books:
            print("Catalog trống. Chạy --refresh để cập nhật.")
            return
        for i, b in enumerate(books, 1):
            status = b.get("status_name", "?")
            ch = b.get("chapter_count", "?")
            print(f"  {i:4d}. [{status:>10s}] {b['name']} ({ch} ch, #{b['id']})")
        print(f"\nTổng: {len(books)} truyện")
        return

    # --- Search ---
    if args.search:
        session = create_session()
        results = search_books(session, args.search)
        if not results:
            print("Không tìm thấy.")
            return
        for b in results:
            ch = b.get("chapter_count", "?")
            print(f"  #{b['id']:>6d}  {b['name']} ({ch} ch)")
        return

    # --- Batch download ---
    if args.all or args.refresh:
        if args.refresh:
            books = refresh_catalog(log_fn=print)
        else:
            books = load_catalog()
        if not books:
            print("Catalog trống!")
            return

        if args.limit:
            books = books[: args.limit]

        status_filter = "hoàn thành" if args.completed else None
        result = download_batch(
            books,
            output_dir=output,
            log_fn=print,
            skip_existing=not args.no_skip,
            status_filter=status_filter,
        )
        print(f"\n{'=' * 50}")
        print(f"Tổng: {result['total']}  ✔{result['ok']}  ✖{result['fail']}  ⊘{result['skipped']}")
        return

    # --- Single book ---
    if args.book or args.id:
        result = download_book(
            book_name=args.book or "",
            ch_start=args.start,
            ch_end=args.end,
            output_dir=output,
            log_fn=print,
            book_id=args.id,
        )
        if not result["success"]:
            print(f"Lỗi: {result.get('reason', '?')}")
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
