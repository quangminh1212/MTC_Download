# TỔNG KẾT PHÂN TÍCH MTC.APK

## 🎯 Mục tiêu
Trích xuất và phân tích MTC.apk để tìm cách tải truyện hàng loạt.

## ✅ Kết quả đạt được

### 1. Phân tích APK thành công
- Giải nén APK bằng unzip
- Tìm được framework: **Flutter**
- Phát hiện API endpoints trong `libapp.so`
- Phân tích file translations để hiểu chức năng app

### 2. API Endpoints đã xác định

**Base URL**: `https://android.lonoapp.net/api`

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/books` | GET | Lấy danh sách truyện | ✅ Hoạt động |
| `/books/{id}` | GET | Chi tiết truyện | ✅ Hoạt động |
| `/chapters` | GET | Danh sách chương (cần book_id) | ✅ Hoạt động |
| `/chapters/{id}` | GET | Nội dung chương | ✅ Hoạt động |

### 3. Scripts đã tạo

| File | Mô tả |
|------|-------|
| `mtc_downloader.py` | Module chính - Class MTCDownloader |
| `download_by_ids.py` | Tải truyện theo danh sách ID |
| `batch_download.py` | Tải truyện tự động (batch) |
| `demo_test.py` | Demo test với truyện ngắn |
| `mtc_api_analysis.py` | Script phân tích API ban đầu |
| `README.md` | Hướng dẫn sử dụng chi tiết |
| `API_ANALYSIS.md` | Báo cáo phân tích đầy đủ |

## 📊 Thông tin API

### Cấu trúc Book Object
```json
{
  "id": 140101,
  "name": "Tên truyện",
  "chapter_count": 189,
  "status_name": "Còn tiếp",
  "synopsis": "Tóm tắt...",
  "poster": {
    "default": "URL ảnh bìa",
    "600": "URL 600px",
    "300": "URL 300px",
    "150": "URL 150px"
  },
  "first_chapter": 21965544,
  "latest_chapter": 27125032,
  "word_count": 483170,
  "review_score": "4.667",
  "bookmark_count": 164
}
```

### Parameters hỗ trợ
- `limit`: Số lượng kết quả (mặc định 100)
- `page`: Trang hiện tại
- `sex`: 1=Nam, 2=Nữ
- `status`: 1=Còn tiếp, 2=Hoàn thành
- `kind`: Loại truyện

## 🚀 Cách sử dụng

### Tải truyện đơn lẻ
```bash
python -c "from mtc_downloader import MTCDownloader; MTCDownloader().download_book(140101)"
```

### Tải nhiều truyện theo ID
```bash
# Chỉnh sửa BOOK_IDS trong download_by_ids.py
python download_by_ids.py
```

### Tải truyện tự động
```bash
python batch_download.py
```

### Test với truyện ngắn
```bash
python demo_test.py
```

## 📁 Cấu trúc output

```
downloads/
├── Thiên Địa Lưu Tiên/
│   ├── info.json           # Metadata truyện
│   ├── chapter_0001.json   # Chương 1
│   ├── chapter_0002.json   # Chương 2
│   └── ...
└── Lãng Nhân Mỹ Nữ/
    ├── info.json
    └── ...
```

## 🔧 Tính năng chính

### MTCDownloader Class
```python
class MTCDownloader:
    def get_books(limit, page, **filters)      # Lấy danh sách truyện
    def get_book_detail(book_id)               # Chi tiết truyện
    def get_chapters(book_id, page, limit)     # Danh sách chương
    def get_chapter_content(chapter_id)        # Nội dung chương
    def download_book(book_id, output_dir)     # Tải một truyện
    def download_multiple_books(book_ids)      # Tải nhiều truyện
```

### Features
- ✅ Tải truyện hàng loạt
- ✅ Lưu metadata (info.json)
- ✅ Xử lý encoding UTF-8 (Windows)
- ✅ Error handling
- ✅ Delay giữa requests
- ✅ Progress tracking
- ✅ Retry logic cơ bản
- ✅ Sanitize filename

## 📈 Test Results

### Truyện test thành công:
1. **Thiên Địa Lưu Tiên** - ID: 140101 (189 chương)
2. **Lãng Nhân: Mỹ Nữ, Mời Tư Vấn** - ID: 140643 (781 chương)
3. **Đấu La: Khí Vận Chi Nữ** - ID: 139039 (690 chương)

### API Response Time:
- `/books`: ~500ms
- `/chapters`: ~300ms
- `/chapters/{id}`: ~200ms

## ⚠️ Lưu ý

1. **Rate Limiting**: Đã thêm delay 0.5-1s giữa requests
2. **Chương khóa**: Một số chương cần đăng nhập/mở khóa
3. **Encoding**: Đã fix UTF-8 cho Windows console
4. **Error Handling**: Script tiếp tục khi gặp lỗi

## 🔮 Mở rộng trong tương lai

### Có thể thêm:
- [ ] Authentication (đăng nhập)
- [ ] Xuất EPUB/PDF
- [ ] GUI interface
- [ ] Progress bar đẹp hơn
- [ ] Resume download
- [ ] Multi-threading
- [ ] Search functionality
- [ ] Filter advanced

## 📝 Files quan trọng từ APK

```
mtc_extracted/
├── lib/arm64-v8a/libapp.so              # Chứa API URLs
├── assets/flutter_assets/
│   └── assets/translations/vi-VN.json   # Chứa tất cả text/features
└── AndroidManifest.xml
```

## 🎓 Kiến thức thu được

1. **Flutter APK Structure**: Hiểu cấu trúc Flutter app
2. **API Reverse Engineering**: Tìm API từ binary
3. **String Extraction**: Dùng grep trên binary files
4. **API Testing**: Test endpoints với curl/requests
5. **Python Scripting**: Viết downloader hoàn chỉnh

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra internet connection
2. Xem log lỗi chi tiết
3. Tăng delay giữa requests
4. Kiểm tra API có thay đổi không

## 🏆 Kết luận

**Đã hoàn thành 100% mục tiêu:**
- ✅ Trích xuất APK
- ✅ Phân tích và tìm API
- ✅ Viết script tải truyện hàng loạt
- ✅ Test thành công
- ✅ Tài liệu đầy đủ

**Scripts sẵn sàng sử dụng ngay!**

---
*Phân tích: 2026-04-17*
*Tool: Claude Code + Python*
*Status: ✅ HOÀN THÀNH*
