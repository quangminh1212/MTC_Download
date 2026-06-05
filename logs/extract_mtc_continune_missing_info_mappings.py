import json
from pathlib import Path

folders = [
"Biên Soạn Tiểu Thuyết Bọn Hắn Đều Cho Là Ta Là Nhân Vật Chính",
"Huyền Huyễn Nguyên Lai Ta Là Tuyệt Thế Võ Thần",
"Hàn Môn Kiêu Sĩ",
"Hàn Môn Quật Khởi Ta Võ Đạo Nghịch Tập Kiếp Sống",
"Hàn Đông Tận Thế Một Cỗ Xe Buýt Lưu Lãng Toàn Cầu",
"Hải Dương Cầu Sinh Từ Bè Gỗ Bắt Đầu Đăng Nhập",
"Hải Dương Tai Biến Bắt Đầu Thức Tỉnh Sss Cấp Thiên Phú",
"Hải Đảo Toàn Dân Thả Câu Ta Độc Lấy Được Sử Thi Thiên Phú",
"Hệ Thống Tu Luyện Ức Vạn Lần",
"Hồng Lâu Xuân",
"Hồng Thủy Tận Thế Ta Tại Huyền Vũ Trên Lưng Xây Gia Viên",
"Không Biết Hàng Lâm Ta Có Vô Địch Lĩnh Vực",
"Không Thể Trường Sinh Ta Không Thể Làm Gì Khác Ngoài Vô Hạn Chuyển Thế",
"Khắc Mệnh Tu Hành Từ Cẩm Y Vệ Bắt Đầu Trường Sinh",
"Kim Bảng Hiện Thế Trẫm Hoàng Hậu Dĩ Nhiên Là Võ Tắc Thiên",
"Kinh Ngạc Của Ta Hoa Quả Toàn Bộ Là Thiên Tài Địa Bảo",
"Ký Túc Xá Cầu Sinh Ta Bị Mặc Định Của Hệ Thống Toàn Tuyển D",
"Toàn Dân Cầu Sinh Không Có Kim Thủ Chỉ Cũng Muốn Cẩu Được",
"Từ Tiên Lại Vững Vàng Thành Đại Thiên Tôn",
]
LOGS = Path(r"C:\Dev\MTC_Download\logs")
OUT = LOGS / "mtc_continune_missing_info_log_mappings.json"
results = {f: [] for f in folders}

def walk(obj, source, stack=None):
    if stack is None:
        stack = []
    if isinstance(obj, dict):
        vals = [v for v in obj.values() if isinstance(v, str)]
        joined = "\n".join(vals)
        for folder in folders:
            if folder in joined:
                entry = {"source": source}
                for key in ("folder", "book_id", "id", "book_name", "name", "remote_total", "remote_count", "downloaded", "status", "expected", "actual", "chapter_count", "local_count", "missing_count", "is_complete", "done_name"):
                    if key in obj:
                        entry[key] = obj[key]
                results[folder].append(entry)
        for v in obj.values():
            walk(v, source, stack)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, source, stack)

for path in LOGS.glob("*.json"):
    if path.name.startswith("mtc_continune_missing_info_log_mappings"):
        continue
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    walk(data, path.name)

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(str(OUT))
for folder, entries in results.items():
    ids=[]
    for e in entries:
        bid=e.get('book_id') or e.get('id')
        if bid and bid not in ids:
            ids.append(bid)
    print(folder, 'entries=', len(entries), 'ids=', ids[:10])
