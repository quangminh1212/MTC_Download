# MTC Downloader - Công cụ tải truyện hàng loạt

## ⚠️ Lưu ý quan trọng

**Thư mục `mtc_extracted/`**: 
- Đây là nội dung APK đã được giải nén để phân tích
- **KHÔNG được sửa đổi** bất kỳ file nào trong thư mục này
- Thư mục này đã được thêm vào `.gitignore` (không commit lên Git)
- Chỉ dùng để tham khảo cấu trúc APK và tìm API endpoints

## Phân tích từ MTC.apk

### API Endpoints đã tìm được:

```
Base URL: https://android.lonoapp.net/api

Endpoints:
- GET /books                    - Lấy danh sách truyện
- GET /books/{id}              - Lấy thông tin chi tiết truyện
- GET /chapters?book_id={id}   - Lấy danh sách chương
- GET /chapters/{id}           - Lấy nội dung chương
```

### Cấu trúc dữ liệu:

**Book Object:**
- `id`: ID truyện
- `name`: Tên truyện
- `slug`: URL slug
- `chapter_count`: Số chương
- `status_name`: Trạng thái (Còn tiếp/Hoàn thành)
- `synopsis`: Tóm tắt nội dung
- `poster`: Ảnh bìa (nhiều kích thước)

**Chapter Object:**
- `id`: ID chương
- `name`: Tên chương
- `content`: Nội dung chương
- `index`: Số thứ tự chương

## Cài đặt

```bash
pip install requests
```

## Sử dụng

### 1. Tải truyện theo ID cụ thể

Chỉnh sửa file `download_by_ids.py`:

```python
BOOK_IDS = [
    140101,  # ID truyện 1
    140643,  # ID truyện 2
    139039,  # ID truyện 3
]
```

Chạy:
```bash
python download_by_ids.py
```

### 2. Tải truyện tự động (batch)

```bash
python batch_download.py
```

Script này sẽ:
- Lấy 20 truyện mới nhất
- Tự động tải 3 truyện đầu tiên

### 3. Sử dụng module MTCDownloader

```python
from mtc_downloader import MTCDownloader

downloader = MTCDownloader()

# Lấy danh sách truyện
books = downloader.get_books(limit=10)

# Tải một truyện
downloader.download_book(book_id=140101, output_dir="downloads", delay=0.5)

# Tải nhiều truyện
book_ids = [140101, 140643, 139039]
downloader.download_multiple_books(book_ids, output_dir="downloads", delay=0.5)
```

## Tham số

- `book_id`: ID của truyện cần tải
- `output_dir`: Thư mục lưu trữ (mặc định: "downloads")
- `delay`: Thời gian chờ giữa các request (giây, mặc định: 1.0)
- `limit`: Số lượng kết quả trả về (mặc định: 100)
- `page`: Trang hiện tại (mặc định: 1)

## Cấu trúc thư mục output

```
downloads/
├── Thiên Địa Lưu Tiên/
│   ├── info.json           # Thông tin truyện
│   ├── chapter_0001.json   # Chương 1
│   ├── chapter_0002.json   # Chương 2
│   └── ...
├── Lãng Nhân Mỹ Nữ/
│   ├── info.json
│   ├── chapter_0001.json
│   └── ...
```

## Lưu ý

1. **Rate Limiting**: Script có delay giữa các request để tránh bị chặn
2. **Encoding**: Đã xử lý encoding UTF-8 cho Windows console
3. **Error Handling**: Script sẽ tiếp tục tải các chương khác nếu một chương bị lỗi
4. **Chương bị khóa**: Một số chương có thể yêu cầu đăng nhập hoặc mở khóa

## Tính năng nâng cao

### Lọc truyện theo tiêu chí

```python
# Lọc theo thể loại, trạng thái, v.v.
books = downloader.get_books(
    limit=50,
    sex=1,        # 1: Nam, 2: Nữ
    status=1,     # 1: Còn tiếp, 2: Hoàn thành
    kind=2        # Loại truyện
)
```

### Xuất sang định dạng khác

Có thể mở rộng để xuất sang:
- TXT
- EPUB
- PDF
- HTML

## API Analysis Summary

### Từ phân tích MTC.apk:

1. **App Framework**: Flutter
2. **API Base**: lonoapp.net
3. **Authentication**: Có hỗ trợ đăng nhập (optional)
4. **Features**:
   - Đọc truyện online
   - Tải truyện offline
   - Mở khóa chương (bằng Khoai/Chìa khóa)
   - Bình luận, đánh giá
   - Đề cử truyện
   - Text-to-Speech

### Files phân tích:

- `mtc_extracted/` - Nội dung APK đã giải nén
- `mtc_extracted/assets/flutter_assets/assets/translations/vi-VN.json` - Bản dịch tiếng Việt
- `mtc_extracted/lib/arm64-v8a/libapp.so` - Flutter compiled code

## Troubleshooting

### Lỗi encoding trên Windows
Script đã tự động xử lý, nhưng nếu vẫn gặp lỗi:
```bash
chcp 65001
python download_by_ids.py
```

### Lỗi kết nối
- Kiểm tra internet
- Tăng timeout trong code
- Giảm số lượng request đồng thời

### Chương tải không được
- Chương có thể bị khóa
- Cần đăng nhập
- Cần mở khóa bằng Khoai/Chìa khóa

## License

Công cụ này chỉ dùng cho mục đích học tập và nghiên cứu.

## Tác giả

Phân tích và phát triển từ MTC.apk
