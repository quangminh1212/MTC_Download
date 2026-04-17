#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Exporter - Xuất truyện sang nhiều định dạng (TXT, EPUB, HTML)
"""

import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import json
from pathlib import Path
from typing import Optional
import html


class MTCExporter:
    """Xuất truyện sang nhiều định dạng"""

    def __init__(self, book_dir: Path):
        self.book_dir = Path(book_dir)
        self.info = self._load_info()
        self.chapters = self._load_chapters()

    def _load_info(self) -> dict:
        """Đọc thông tin truyện"""
        info_file = self.book_dir / "info.json"
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_chapters(self) -> list:
        """Đọc tất cả chương"""
        chapter_files = sorted(self.book_dir.glob("chapter_*.json"))
        chapters = []

        for chapter_file in chapter_files:
            try:
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    chapters.append(json.load(f))
            except Exception as e:
                print(f"⚠️ Lỗi đọc {chapter_file.name}: {e}")

        return chapters

    def export_txt(self, output_file: Optional[Path] = None) -> bool:
        """Xuất sang TXT"""
        if not output_file:
            output_file = self.book_dir / "full_book.txt"

        print(f"\n📝 Xuất TXT: {output_file.name}")

        book_name = self.info.get('name', 'Unknown')
        author = self.info.get('author', 'Unknown')
        synopsis = self.info.get('synopsis', '')

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 60 + "\n")
                f.write(f"{book_name}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Tác giả: {author}\n\n")

                if synopsis:
                    f.write("Tóm tắt:\n")
                    f.write(synopsis + "\n\n")

                f.write("=" * 60 + "\n\n")

                # Nội dung
                for idx, chapter in enumerate(self.chapters, 1):
                    chapter_name = chapter.get('name', f'Chương {idx}')
                    content = chapter.get('content', '')

                    f.write(f"\n{'=' * 60}\n")
                    f.write(f"{chapter_name}\n")
                    f.write(f"{'=' * 60}\n\n")
                    f.write(content)
                    f.write("\n\n")

                    print(f"  [{idx}/{len(self.chapters)}] ✅ {chapter_name}")

            print(f"✅ Đã xuất {len(self.chapters)} chương")
            return True

        except Exception as e:
            print(f"❌ Lỗi xuất TXT: {e}")
            return False

    def export_html(self, output_file: Optional[Path] = None) -> bool:
        """Xuất sang HTML"""
        if not output_file:
            output_file = self.book_dir / "full_book.html"

        print(f"\n🌐 Xuất HTML: {output_file.name}")

        book_name = self.info.get('name', 'Unknown')
        author = self.info.get('author', 'Unknown')
        synopsis = self.info.get('synopsis', '')

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # HTML Header
                f.write("""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.8;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .author {{
            color: #7f8c8d;
            font-style: italic;
        }}
        .synopsis {{
            background: #ecf0f1;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 20px 0;
        }}
        .chapter {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .chapter-title {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .content {{
            text-align: justify;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{}</h1>
        <p class="author">Tác giả: {}</p>
        {}
    </div>
""".format(
                    html.escape(book_name),
                    html.escape(book_name),
                    html.escape(author),
                    f'<div class="synopsis"><strong>Tóm tắt:</strong><br>{html.escape(synopsis)}</div>' if synopsis else ''
                ))

                # Chapters
                for idx, chapter in enumerate(self.chapters, 1):
                    chapter_name = chapter.get('name', f'Chương {idx}')
                    content = chapter.get('content', '')

                    f.write(f"""
    <div class="chapter">
        <h2 class="chapter-title">{html.escape(chapter_name)}</h2>
        <div class="content">{html.escape(content)}</div>
    </div>
""")
                    print(f"  [{idx}/{len(self.chapters)}] ✅ {chapter_name}")

                # HTML Footer
                f.write("""
</body>
</html>
""")

            print(f"✅ Đã xuất {len(self.chapters)} chương")
            return True

        except Exception as e:
            print(f"❌ Lỗi xuất HTML: {e}")
            return False

    def export_markdown(self, output_file: Optional[Path] = None) -> bool:
        """Xuất sang Markdown"""
        if not output_file:
            output_file = self.book_dir / "full_book.md"

        print(f"\n📄 Xuất Markdown: {output_file.name}")

        book_name = self.info.get('name', 'Unknown')
        author = self.info.get('author', 'Unknown')
        synopsis = self.info.get('synopsis', '')

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Header
                f.write(f"# {book_name}\n\n")
                f.write(f"**Tác giả:** {author}\n\n")

                if synopsis:
                    f.write("## Tóm tắt\n\n")
                    f.write(f"{synopsis}\n\n")

                f.write("---\n\n")

                # Chapters
                for idx, chapter in enumerate(self.chapters, 1):
                    chapter_name = chapter.get('name', f'Chương {idx}')
                    content = chapter.get('content', '')

                    f.write(f"## {chapter_name}\n\n")
                    f.write(f"{content}\n\n")
                    f.write("---\n\n")

                    print(f"  [{idx}/{len(self.chapters)}] ✅ {chapter_name}")

            print(f"✅ Đã xuất {len(self.chapters)} chương")
            return True

        except Exception as e:
            print(f"❌ Lỗi xuất Markdown: {e}")
            return False

    def export_all(self):
        """Xuất tất cả định dạng"""
        print(f"\n{'='*60}")
        print(f"📦 Xuất truyện: {self.info.get('name', 'Unknown')}")
        print(f"{'='*60}")

        formats = [
            ('TXT', self.export_txt),
            ('HTML', self.export_html),
            ('Markdown', self.export_markdown),
        ]

        results = {}
        for format_name, export_func in formats:
            try:
                results[format_name] = export_func()
            except Exception as e:
                print(f"❌ Lỗi xuất {format_name}: {e}")
                results[format_name] = False

        # Tổng kết
        print(f"\n{'='*60}")
        print("📊 Kết quả xuất:")
        for format_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {format_name}")
        print(f"{'='*60}\n")


def main():
    """Demo export"""
    import sys

    if len(sys.argv) < 2:
        print("Sử dụng: python mtc_exporter.py <thư_mục_truyện>")
        print("\nVí dụ:")
        print("  python mtc_exporter.py downloads/Thiên_Địa_Lưu_Tiên")
        return

    book_dir = Path(sys.argv[1])

    if not book_dir.exists():
        print(f"❌ Không tìm thấy thư mục: {book_dir}")
        return

    exporter = MTCExporter(book_dir)
    exporter.export_all()


if __name__ == "__main__":
    main()
