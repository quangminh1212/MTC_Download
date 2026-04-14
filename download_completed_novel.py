#!/usr/bin/env python3
"""Download a completed novel to downloads folder (mock version)."""
from pathlib import Path
from mtc.utils import safe_name, ensure_dir

# Mock completed novel
COMPLETED_NOVEL = {
    "id": 88888,
    "name": "Kiếm Đạo Độc Tôn",
    "status_name": "Hoàn thành",
    "chapter_count": 15,
    "author": "Tác giả A",
    "synopsis": "Một câu chuyện về hành trình tu kiếm đạo..."
}

CHAPTERS = [
    {"id": 1, "title": "Chương 1: Thiếu niên kiếm khách"},
    {"id": 2, "title": "Chương 2: Nhập môn kiếm tông"},
    {"id": 3, "title": "Chương 3: Luyện kiếm cơ bản"},
    {"id": 4, "title": "Chương 4: Gặp sư tỷ"},
    {"id": 5, "title": "Chương 5: Đại hội môn phái"},
    {"id": 6, "title": "Chương 6: Chiến thắng"},
    {"id": 7, "title": "Chương 7: Nhận nhiệm vụ"},
    {"id": 8, "title": "Chương 8: Vào rừng sâu"},
    {"id": 9, "title": "Chương 9: Gặp yêu thú"},
    {"id": 10, "title": "Chương 10: Đột phá tu vi"},
    {"id": 11, "title": "Chương 11: Tìm kiếm bảo vật"},
    {"id": 12, "title": "Chương 12: Đại chiến ma đạo"},
    {"id": 13, "title": "Chương 13: Lĩnh ngộ kiếm ý"},
    {"id": 14, "title": "Chương 14: Quyết chiến"},
    {"id": 15, "title": "Chương 15: Viên mãn (Hoàn)"},
]

CONTENT_TEMPLATE = """
Linh khí thiên địa tụ tập, kiếm quang lóe sáng.

Chủ nhân công ngồi thiền định, tu luyện kiếm quyết.

Sau một đêm khổ luyện, kiếm ý tinh thuần hơn.

"Ta sẽ trở thành kiếm tu mạnh nhất!"

--- Hết chương ---
"""

def main():
    DOWNLOAD_DIR = Path(__file__).parent / "downloads"
    
    print(f"📥 Tải truyện hoàn thành vào: {DOWNLOAD_DIR}")
    print("=" * 60)
    
    book_name = COMPLETED_NOVEL["name"]
    print(f"📖 {book_name} (ID: {COMPLETED_NOVEL['id']})")
    print(f"   ✅ Trạng thái: {COMPLETED_NOVEL['status_name']}")
    print(f"   📊 Số chương: {COMPLETED_NOVEL['chapter_count']}")
    
    # Create book directory
    book_dir = ensure_dir(DOWNLOAD_DIR / safe_name(book_name))
    print(f"   📁 Thư mục: {book_dir}")
    
    # Download chapters
    print(f"\n   Đang tải {len(CHAPTERS)} chương...")
    for chapter in CHAPTERS:
        ch_title = chapter["title"]
        ch_file = book_dir / f"{safe_name(ch_title)}.txt"
        
        # Write content
        content = f"{ch_title}\n{CONTENT_TEMPLATE}"
        ch_file.write_text(content, encoding="utf-8")
        print(f"   ✓ {safe_name(ch_title)}.txt")
    
    print(f"\n✅ Hoàn thành!")
    print(f"   Đã tải: {len(CHAPTERS)}/{COMPLETED_NOVEL['chapter_count']} chương")
    print(f"   Vị trí: {book_dir}")
    
    # List files
    print(f"\n📁 Danh sách file:")
    for f in sorted(book_dir.glob("*.txt")):
        size = f.stat().st_size
        print(f"   {f.name} ({size} bytes)")

if __name__ == "__main__":
    main()
