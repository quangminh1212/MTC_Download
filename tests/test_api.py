"""Test API availability for novels in library."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mtc.pipeline import _api_session, _resolve_book, _fetch_chapter_list, _HAS_API_DEPS

if not _HAS_API_DEPS:
    print("API deps not available (requests/pycryptodome/ftfy)")
    sys.exit(1)

session = _api_session()

test_books = [
    "Có Được Bất Tử Kỹ Ta Có Thể Vô Hạn Load",
    "Tận Thế Chi Siêu Thị Hệ Thống",
    "Conan: Coi Là Chân Tửu Cùng Mori Ran Trao Đổi Cơ Thể",
    "Ta Có Trăm Vạn Điểm Kỹ Năng",
    "Nhất Kiếm Bá Thiên",
    "Để Ngươi Người Quản Lý Phế Vật Lớp, Làm Sao Thành Võ Thần Điện",
    "Ta Treo Máy Ngàn Vạn Năm",
    "Mạt Thế Vô Hạn Thôn Phệ",
]

for name in test_books:
    try:
        book = _resolve_book(session, name)
        if book:
            chapters = _fetch_chapter_list(session, book["id"])
            print(f"API OK: {name} -> id={book['id']}, name={book.get('name','?')}, chapters={len(chapters)}")
        else:
            print(f"API NOT FOUND: {name}")
    except Exception as e:
        print(f"API ERROR: {name} -> {e}")
