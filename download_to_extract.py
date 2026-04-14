#!/usr/bin/env python3
"""Download novels directly to extract folder."""
import sys
from pathlib import Path
from mtc.config import log
from mtc.downloader import download_book

# Set output to extract folder
EXTRACT_DIR = Path(__file__).parent / "extract" / "novels"

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_to_extract.py <book_name_or_id>")
        print("Example: python download_to_extract.py 'Tên Truyện'")
        print("Example: python download_to_extract.py --id 12345")
        return
    
    book_id = None
    book_name = ""
    
    # Parse arguments
    if "--id" in sys.argv:
        idx = sys.argv.index("--id")
        if idx + 1 < len(sys.argv):
            book_id = int(sys.argv[idx + 1])
    else:
        book_name = " ".join(sys.argv[1:])
    
    print(f"📥 Tải truyện vào: {EXTRACT_DIR}")
    print("=" * 60)
    
    result = download_book(
        book_name=book_name,
        book_id=book_id,
        output_dir=EXTRACT_DIR,
        log_fn=print,
    )
    
    if result["success"]:
        print("\n✅ Tải thành công!")
        print(f"   Truyện: {result['book_name']}")
        print(f"   Số chương: {result['chapters']}")
        print(f"   Vị trí: {EXTRACT_DIR / result['book_name']}")
    else:
        print(f"\n❌ Lỗi: {result.get('reason', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
