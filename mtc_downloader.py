#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Downloader - Tải truyện hàng loạt từ MTC API
Phân tích từ MTC.apk

API Endpoints:
- Base: https://android.lonoapp.net/api
- Books: /books
- Chapters: /chapters (cần book_id)
- Chapter detail: /chapters/{id}
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Optional

class MTCDownloader:
    def __init__(self):
        self.base_url = "https://android.lonoapp.net/api"
        self.headers = {
            "User-Agent": "MTC/Android",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_books(self, limit=100, page=1, **filters) -> Optional[Dict]:
        """Lấy danh sách truyện"""
        if limit < 5:
            limit = 5
        url = f"{self.base_url}/books"
        params = {"limit": limit, "page": page, **filters}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách truyện: {e}")
            return None

    def get_book_detail(self, book_id: int) -> Optional[Dict]:
        """Lấy thông tin chi tiết truyện"""
        url = f"{self.base_url}/books/{book_id}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin truyện {book_id}: {e}")
            return None

    def get_chapters(self, book_id: int, page=1, limit=100) -> Optional[Dict]:
        """Lấy danh sách chương của truyện"""
        url = f"{self.base_url}/chapters"
        params = {
            "filter[book_id]": book_id,
            "page": page,
            "limit": limit
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách chương: {e}")
            return None

    def get_chapter_content(self, chapter_id: int) -> Optional[Dict]:
        """Lấy nội dung chương"""
        url = f"{self.base_url}/chapters/{chapter_id}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Lỗi khi tải chương {chapter_id}: {e}")
            return None

    def download_book(self, book_id: int, output_dir="downloads", delay=1.0):
        """Tải toàn bộ truyện"""
        print(f"\n{'='*60}")
        print(f"📚 Bắt đầu tải truyện ID: {book_id}")
        print(f"{'='*60}")

        # Lấy thông tin truyện
        book_info = self.get_book_detail(book_id)
        if not book_info:
            print("❌ Không thể lấy thông tin truyện")
            return False

        book_data = book_info.get("data", {})
        book_name = book_data.get("name", f"book_{book_id}")
        chapter_count = book_data.get("chapter_count") or book_data.get("latest_index", 0)

        print(f"📖 Tên truyện: {book_name}")
        print(f"📊 Tổng số chương: {chapter_count}")

        # Tạo thư mục lưu trữ
        book_dir = Path(output_dir) / self.sanitize_filename(book_name)
        book_dir.mkdir(parents=True, exist_ok=True)

        # Lưu thông tin truyện
        with open(book_dir / "info.json", "w", encoding="utf-8") as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2)

        # Lấy danh sách chương
        all_chapters = []
        page = 1

        while True:
            print(f"📄 Đang lấy danh sách chương (trang {page})...")
            chapters_data = self.get_chapters(book_id, page=page, limit=100)

            if not chapters_data or "data" not in chapters_data:
                break

            chapters = chapters_data["data"]
            if not chapters:
                break

            all_chapters.extend(chapters)

            # Kiểm tra xem còn trang nào không
            if len(chapters) < 100:
                break

            page += 1
            time.sleep(delay)

        print(f"✅ Tìm thấy {len(all_chapters)} chương")

        # Tải từng chương
        success_count = 0
        failed_chapters = []

        for idx, chapter in enumerate(all_chapters, 1):
            chapter_id = chapter.get("id")
            chapter_name = chapter.get("name", f"Chương {idx}")

            print(f"[{idx}/{len(all_chapters)}] 📥 Đang tải: {chapter_name}...", end=" ")

            content = self.get_chapter_content(chapter_id)

            if content and "data" in content:
                chapter_file = book_dir / f"chapter_{idx:04d}.json"
                with open(chapter_file, "w", encoding="utf-8") as f:
                    json.dump(content["data"], f, ensure_ascii=False, indent=2)

                print("✅")
                success_count += 1
            else:
                print("❌")
                failed_chapters.append((idx, chapter_name, chapter_id))

            time.sleep(delay)

        # Tổng kết
        print(f"\n{'='*60}")
        print(f"✅ Hoàn thành tải truyện: {book_name}")
        print(f"📊 Thành công: {success_count}/{len(all_chapters)} chương")

        if failed_chapters:
            print(f"❌ Thất bại: {len(failed_chapters)} chương")
            print("\nDanh sách chương lỗi:")
            for idx, name, cid in failed_chapters:
                print(f"  - Chương {idx}: {name} (ID: {cid})")

        print(f"💾 Đã lưu vào: {book_dir}")
        print(f"{'='*60}\n")

        return success_count > 0

    def download_multiple_books(self, book_ids: List[int], output_dir="downloads", delay=1.0):
        """Tải nhiều truyện"""
        print(f"\n🚀 Bắt đầu tải {len(book_ids)} truyện")

        for idx, book_id in enumerate(book_ids, 1):
            print(f"\n[{idx}/{len(book_ids)}] Đang xử lý truyện ID: {book_id}")
            self.download_book(book_id, output_dir, delay)

            if idx < len(book_ids):
                print(f"⏳ Chờ {delay*2} giây trước khi tải truyện tiếp theo...")
                time.sleep(delay * 2)

        print("\n🎉 Hoàn thành tải tất cả truyện!")

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Làm sạch tên file"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()


def main():
    # Fix encoding for Windows console
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    downloader = MTCDownloader()

    print("="*60)
    print("MTC DOWNLOADER - Tải truyện hàng loạt")
    print("="*60)

    # Test: Lấy danh sách truyện mới nhất
    print("\n📚 Đang lấy danh sách truyện mới nhất...")
    books = downloader.get_books(limit=10)

    if books and "data" in books:
        print(f"\n✅ Tìm thấy {len(books['data'])} truyện:\n")

        for idx, book in enumerate(books["data"], 1):
            print(f"{idx}. {book['name']}")
            print(f"   ID: {book['id']}")
            print(f"   Số chương: {book['chapter_count']}")
            print(f"   Trạng thái: {book['status_name']}")
            print()

        # Ví dụ: Tải truyện đầu tiên
        first_book_id = books["data"][0]["id"]

        choice = input(f"\n💡 Bạn có muốn tải truyện đầu tiên (ID: {first_book_id})? (y/n): ")

        if choice.lower() == 'y':
            downloader.download_book(first_book_id, delay=0.5)
    else:
        print("❌ Không thể lấy danh sách truyện")


if __name__ == "__main__":
    main()
