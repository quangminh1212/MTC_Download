# Hướng dẫn sử dụng MTC Downloader

## 🚀 Cài đặt nhanh

```bash
pip install requests
```

## 📖 Các cách sử dụng

### 1. Giao diện CLI tương tác (Khuyến nghị)

```bash
python mtc_cli.py
```

**Tính năng:**
- Tìm kiếm truyện theo tên
- Xem danh sách truyện mới
- Tải truyện theo ID
- Tải nhiều truyện cùng lúc
- Giao diện menu dễ sử dụng

### 2. Tải và xuất tự động

```bash
python auto_download_export.py
```

**Tính năng:**
- Tải truyện và tự động xuất sang TXT, HTML, Markdown
- Xử lý hàng loạt nhiều truyện
- Báo cáo kết quả chi tiết

### 3. Tải theo danh sách ID

Chỉnh sửa `download_by_ids.py`:

```python
BOOK_IDS = [
    140101,  # Thiên Địa Lưu Tiên
    140643,  # Lãng Nhân Mỹ Nữ
    139039,  # Truyện khác
]
```

Chạy:
```bash
python download_by_ids.py
```

### 4. Xuất file từ truyện đã tải

```bash
python mtc_exporter.py downloads/Tên_Truyện
```

**Định dạng hỗ trợ:**
- TXT - Văn bản thuần
- HTML - Trang web đẹp mắt
- Markdown - Định dạng MD

### 5. Sử dụng như module Python

```python
from mtc_downloader import MTCDownloader
from mtc_exporter import MTCExporter

# Tải truyện
downloader = MTCDownloader()
downloader.download_book(140101, output_dir="downloads", delay=0.5)

# Xuất file
exporter = MTCExporter("downloads/Thiên_Địa_Lưu_Tiên")
exporter.export_txt()
exporter.export_html()
```

## 📁 Cấu trúc thư mục

```
downloads/
├── Thiên_Địa_Lưu_Tiên/
│   ├── info.json           # Thông tin truyện
│   ├── chapter_0001.json   # Chương 1
│   ├── chapter_0002.json   # Chương 2
│   ├── ...
│   ├── full_book.txt       # File TXT đầy đủ
│   ├── full_book.html      # File HTML đẹp
│   └── full_book.md        # File Markdown
```

## ⚙️ Tham số cấu hình

### MTCDownloader

```python
downloader = MTCDownloader()

# Lấy danh sách truyện
books = downloader.get_books(
    limit=100,      # Số lượng truyện
    page=1,         # Trang hiện tại
    sex=1,          # 1: Nam, 2: Nữ
    status=1,       # 1: Còn tiếp, 2: Hoàn thành
)

# Tải truyện
downloader.download_book(
    book_id=140101,
    output_dir="downloads",
    delay=0.5       # Delay giữa các request (giây)
)
```

### MTCExporter

```python
exporter = MTCExporter("downloads/Tên_Truyện")

# Xuất từng định dạng
exporter.export_txt()
exporter.export_html()
exporter.export_markdown()

# Hoặc xuất tất cả
exporter.export_all()
```

## 💡 Tips & Tricks

### Tải nhanh nhiều truyện

```python
from auto_download_export import AutoDownloadExport

processor = AutoDownloadExport(delay=0.3)  # Giảm delay
book_ids = [140101, 140643, 139039]
processor.process_multiple(book_ids, export_formats=['txt'])
```

### Tìm truyện theo từ khóa

```python
from mtc_cli import MTCCLI

cli = MTCCLI()
results = cli.search_books("tu tiên")  # Tìm truyện tu tiên
```

### Lọc truyện theo tiêu chí

```python
# Truyện nam, hoàn thành
books = downloader.get_books(sex=1, status=2, limit=50)

# Truyện nữ, còn tiếp
books = downloader.get_books(sex=2, status=1, limit=50)
```

## 🔧 Xử lý lỗi

### Lỗi encoding trên Windows

```bash
chcp 65001
python mtc_cli.py
```

### Lỗi kết nối

- Kiểm tra internet
- Tăng delay: `delay=1.0` hoặc cao hơn
- Thử lại sau vài phút

### Chương tải không được

Một số chương có thể:
- Bị khóa (cần mở khóa)
- Yêu cầu đăng nhập
- Chưa được xuất bản

## 📊 Ví dụ thực tế

### Tải top 10 truyện mới và xuất HTML

```python
from mtc_downloader import MTCDownloader
from mtc_exporter import MTCExporter
from pathlib import Path

downloader = MTCDownloader()

# Lấy 10 truyện mới
books = downloader.get_books(limit=10)

for book in books['data'][:3]:  # Tải 3 truyện đầu
    book_id = book['id']
    book_name = book['name']
    
    print(f"Đang tải: {book_name}")
    downloader.download_book(book_id, delay=0.5)
    
    # Xuất HTML
    book_dir = Path("downloads") / downloader.sanitize_filename(book_name)
    exporter = MTCExporter(book_dir)
    exporter.export_html()
```

### Tải truyện yêu thích

```python
# Danh sách truyện yêu thích
favorites = {
    "Thiên Địa Lưu Tiên": 140101,
    "Lãng Nhân Mỹ Nữ": 140643,
    "Truyện khác": 139039,
}

for name, book_id in favorites.items():
    print(f"Tải: {name}")
    downloader.download_book(book_id)
```

## 🎯 Workflow khuyến nghị

1. **Khám phá truyện**: Dùng `mtc_cli.py` để tìm và xem truyện
2. **Tải hàng loạt**: Dùng `auto_download_export.py` để tải và xuất
3. **Đọc offline**: Mở file HTML trong trình duyệt hoặc TXT trong notepad

## ⚠️ Lưu ý

- **Rate limiting**: Có delay giữa các request để tránh bị chặn
- **Dung lượng**: Mỗi truyện có thể chiếm 5-50MB tùy số chương
- **Bản quyền**: Chỉ dùng cho mục đích cá nhân, học tập

## 🆘 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra kết nối internet
2. Đảm bảo đã cài `requests`: `pip install requests`
3. Chạy với Python 3.7+
4. Xem log lỗi để biết chi tiết

## 📝 Changelog

- **v1.0**: Tải truyện cơ bản
- **v1.1**: Thêm CLI tương tác
- **v1.2**: Xuất HTML, Markdown
- **v1.3**: Tải và xuất tự động
