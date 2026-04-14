#!/usr/bin/env python3
"""Test download with mock data."""
from pathlib import Path
from mtc.utils import safe_name, ensure_dir

# Mock data
MOCK_BOOK = {
    "id": 12345,
    "name": "Truyện Test Hoàn Thành",
    "status_name": "Hoàn thành",
    "chapter_count": 5
}

MOCK_CHAPTERS = [
    {"id": 1, "title": "Chương 1: Khởi đầu"},
    {"id": 2, "title": "Chương 2: Phát triển"},
    {"id": 3, "title": "Chương 3: Cao trào"},
    {"id": 4, "title": "Chương 4: Hồi kết"},
    {"id": 5, "title": "Chương 5: Kết thúc"},
]

MOCK_CONTENT = """Đây là nội dung chương test.

Đoạn văn thứ nhất với nội dung mẫu.

Đoạn văn thứ hai với nội dung mẫu.

--- Hết chương ---
"""

def test_download():
    """Test download structure."""
    EXTRACT_DIR = Path(__file__).parent / "extract" / "novels"
    
    print(f"📥 Test tải truyện vào: {EXTRACT_DIR}")
    print("=" * 60)
    
    book_name = MOCK_BOOK["name"]
    print(f"📖 {book_name} (ID: {MOCK_BOOK['id']})")
    print(f"   Trạng thái: {MOCK_BOOK['status_name']}")
    print(f"   Số chương: {MOCK_BOOK['chapter_count']}")
    
    # Create book directory
    book_dir = ensure_dir(EXTRACT_DIR / safe_name(book_name))
    print(f"   Thư mục: {book_dir}")
    
    # Download chapters
    print(f"\n   Đang tải {len(MOCK_CHAPTERS)} chương...")
    for i, chapter in enumerate(MOCK_CHAPTERS, 1):
        ch_title = chapter["title"]
        ch_file = book_dir / f"{i:04d}_{safe_name(ch_title)}.txt"
        
        # Write content
        content = f"{ch_title}\n\n{MOCK_CONTENT}"
        ch_file.write_text(content, encoding="utf-8")
        print(f"   ✓ {i:04d}_{safe_name(ch_title)}.txt")
    
    print(f"\n✅ Hoàn thành!")
    print(f"   Đã tải: {len(MOCK_CHAPTERS)} chương")
    print(f"   Vị trí: {book_dir}")
    
    # List files
    print(f"\n📁 Danh sách file:")
    for f in sorted(book_dir.glob("*.txt")):
        size = f.stat().st_size
        print(f"   {f.name} ({size} bytes)")

if __name__ == "__main__":
    test_download()
