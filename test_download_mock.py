#!/usr/bin/env python3
"""Test download with mock data."""
from pathlib import Path
from mtc.utils import safe_name, ensure_dir

# Mock data - Truyện hoàn thành
MOCK_BOOK = {
    "id": 99999,
    "name": "Võ Luyện Đỉnh Phong - Hoàn Thành",
    "status_name": "Hoàn thành",
    "chapter_count": 10,
    "author": "Tác giả test",
    "synopsis": "Một câu chuyện về hành trình tu luyện đến đỉnh cao võ đạo..."
}

MOCK_CHAPTERS = [
    {"id": 1, "title": "Chương 1: Khởi đầu hành trình"},
    {"id": 2, "title": "Chương 2: Gặp gỡ sư phụ"},
    {"id": 3, "title": "Chương 3: Tu luyện võ công"},
    {"id": 4, "title": "Chương 4: Đại chiến ma đạo"},
    {"id": 5, "title": "Chương 5: Đột phá cảnh giới"},
    {"id": 6, "title": "Chương 6: Vào bí cảnh"},
    {"id": 7, "title": "Chương 7: Tìm được bảo vật"},
    {"id": 8, "title": "Chương 8: Quyết chiến kẻ thù"},
    {"id": 9, "title": "Chương 9: Đăng đỉnh võ đạo"},
    {"id": 10, "title": "Chương 10: Viên mãn kết thúc"},
]

MOCK_CONTENT = """Nội dung chương truyện võ hiệp...

Thiên địa linh khí tụ tập, chủ nhân công bắt đầu tu luyện.

Sau một đêm khổ công, công lực tăng thêm một tầng.

Bỗng nhiên, một tiếng nổ vang lên từ xa...

"Ai dám phá đảo tu luyện của ta?"

Chủ nhân công mở mắt, ánh mắt sắc bén như kiếm.

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
