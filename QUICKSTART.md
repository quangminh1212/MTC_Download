# HƯỚNG DẪN SỬ DỤNG NHANH

## Bước 1: Cài đặt

### Windows:
```bash
setup.bat
```

### Linux/Mac:
```bash
pip install -r requirements.txt
```

## Bước 2: Sử dụng

### 🎯 Cách 1: Tải theo ID truyện (Khuyến nghị)

1. Mở file `download_by_ids.py`
2. Sửa danh sách ID truyện:
```python
BOOK_IDS = [
    140101,  # Thiên Địa Lưu Tiên
    140643,  # Lãng Nhân: Mỹ Nữ
    139039,  # Đấu La
]
```
3. Chạy:
```bash
python download_by_ids.py
```

### 🚀 Cách 2: Tải tự động

Tải 3 truyện mới nhất:
```bash
python batch_download.py
```

### 🧪 Cách 3: Test với truyện ngắn

```bash
python demo_test.py
```

### 📝 Cách 4: Tải + Export TXT

```bash
python advanced_downloader.py
```

## Tìm ID truyện

### Cách 1: Từ URL
```
https://vtruyen.com/truyen/thien-dia-luu-tien
→ Tìm ID trong API hoặc inspect network
```

### Cách 2: Dùng Python
```python
from mtc_downloader import MTCDownloader

downloader = MTCDownloader()
books = downloader.get_books(limit=50)

for book in books["data"]:
    print(f"ID: {book['id']:6d} - {book['name']}")
```

### Cách 3: Lọc truyện
```python
# Truyện nam, đang ra, nhiều chương
books = downloader.get_books(
    limit=100,
    sex=1,      # 1=Nam, 2=Nữ
    status=1    # 1=Còn tiếp, 2=Hoàn thành
)

# Sắp xếp theo số chương
sorted_books = sorted(
    books["data"], 
    key=lambda x: x["chapter_count"], 
    reverse=True
)

for book in sorted_books[:10]:
    print(f"ID: {book['id']} - {book['name']} - {book['chapter_count']} chương")
```

## Kết quả

Truyện được lưu trong thư mục `downloads/`:

```
downloads/
├── Thiên Địa Lưu Tiên/
│   ├── info.json           # Thông tin truyện
│   ├── chapter_0001.json   # Chương 1
│   ├── chapter_0002.json   # Chương 2
│   ├── ...
│   └── full_book.txt       # (nếu dùng advanced_downloader)
```

## Đọc nội dung

### Đọc từ JSON:
```python
import json

with open("downloads/Thiên Địa Lưu Tiên/chapter_0001.json", "r", encoding="utf-8") as f:
    chapter = json.load(f)
    print(chapter["name"])
    print(chapter["content"])
```

### Đọc từ TXT:
```
Mở file: downloads/Thiên Địa Lưu Tiên/full_book.txt
```

## Tùy chỉnh

### Thay đổi delay (tránh bị chặn):
```python
downloader.download_book(
    book_id=140101,
    delay=1.0  # Chờ 1 giây giữa các request
)
```

### Thay đổi thư mục lưu:
```python
downloader.download_book(
    book_id=140101,
    output_dir="my_books"
)
```

### Tải nhiều truyện:
```python
book_ids = [140101, 140643, 139039, 153384, 153347]
downloader.download_multiple_books(
    book_ids=book_ids,
    output_dir="downloads",
    delay=0.5
)
```

## Xử lý lỗi

### Lỗi: "UnicodeEncodeError"
```bash
# Windows: Chạy trước
chcp 65001

# Hoặc dùng setup.bat
```

### Lỗi: "Connection timeout"
- Kiểm tra internet
- Tăng delay lên 2-3 giây
- Thử lại sau

### Lỗi: "Chapter not found"
- Chương có thể bị khóa
- Cần đăng nhập
- Bỏ qua và tiếp tục

## Tips

1. **Tải truyện ngắn trước** để test
2. **Tăng delay** nếu tải nhiều truyện
3. **Backup** thư mục downloads thường xuyên
4. **Kiểm tra** info.json để xem metadata
5. **Export TXT** để đọc dễ hơn

## Ví dụ hoàn chỉnh

```python
from mtc_downloader import MTCDownloader

# Khởi tạo
downloader = MTCDownloader()

# Tìm truyện hay
books = downloader.get_books(limit=100, sex=1, status=1)

# Lọc truyện có điểm cao
good_books = [
    b for b in books["data"] 
    if float(b.get("review_score", 0)) >= 4.5
]

# In danh sách
print("Truyện điểm cao:")
for book in good_books[:10]:
    print(f"- {book['name']} ({book['review_score']} ⭐)")

# Tải top 3
top_ids = [b["id"] for b in good_books[:3]]
downloader.download_multiple_books(top_ids, delay=1.0)
```

## Hỗ trợ

Gặp vấn đề? Kiểm tra:
1. `README.md` - Hướng dẫn chi tiết
2. `API_ANALYSIS.md` - Thông tin API
3. `SUMMARY.md` - Tổng kết dự án

---
*Chúc bạn tải truyện vui vẻ! 📚*
