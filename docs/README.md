# Tài liệu hướng dẫn

## Tổng quan

Dự án này cung cấp công cụ để tải truyện từ API, nhưng gặp vấn đề **nội dung bị mã hóa** bằng Laravel Encryption (AES-256-CBC).

## Vấn đề hiện tại

- ✅ API hoạt động bình thường
- ✅ Có thể lấy danh sách truyện và chapter
- ❌ Nội dung chapter bị mã hóa (cần APP_KEY để giải mã)

## Giải pháp

Có 4 phương án để tìm APP_KEY và giải mã nội dung:

### 1. 🔍 Dùng mitmproxy (KHUYẾN NGHỊ)
- **Độ khó**: ⭐⭐
- **Thời gian**: 30-60 phút
- **Tỷ lệ thành công**: 80%
- **Hướng dẫn**: [MITMPROXY_GUIDE.md](MITMPROXY_GUIDE.md)

### 2. 🔧 Dùng reFlutter
- **Độ khó**: ⭐⭐
- **Thời gian**: 1-2 giờ
- **Tỷ lệ thành công**: 60%
- **Hướng dẫn**: [DART_DECOMPILE_GUIDE.md](DART_DECOMPILE_GUIDE.md)

### 3. 🎯 Dùng Frida Hook
- **Độ khó**: ⭐⭐⭐
- **Thời gian**: 2-3 giờ
- **Tỷ lệ thành công**: 70%
- **Hướng dẫn**: [MITMPROXY_GUIDE.md](MITMPROXY_GUIDE.md) (phần Frida)

### 4. 🛠️ Phân tích với Ghidra
- **Độ khó**: ⭐⭐⭐⭐
- **Thời gian**: 4-8 giờ
- **Tỷ lệ thành công**: 40%
- **Hướng dẫn**: [DART_DECOMPILE_GUIDE.md](DART_DECOMPILE_GUIDE.md)

## Quick Start

```bash
# Bắt đầu với phương án dễ nhất
pip install mitmproxy
mitmweb

# Cấu hình điện thoại Android để dùng proxy
# Xem hướng dẫn chi tiết trong MITMPROXY_GUIDE.md
```

## Scripts có sẵn

### Phân tích và tìm kiếm
- `find_encryption_key.py` - Tìm key trong APK
- `extract_strings.py` - Extract strings từ libapp.so
- `find_urls.py` - Tìm URLs trong strings

### Decompile và phân tích
- `extract_dart_snapshot.py` - Extract Dart snapshot từ libapp.so
- `analyze_dart_snapshot.py` - Phân tích snapshot để tìm keys

### Network analysis
- `analyze_mitmproxy_traffic.py` - Phân tích traffic từ mitmproxy

### Testing
- `test_decrypt_with_key.py` - Test giải mã khi có APP_KEY

## Khi tìm được APP_KEY

1. Test ngay:
```bash
python test_decrypt_with_key.py "base64:YOUR_KEY_HERE"
```

2. Tích hợp vào downloader:
   - Sửa file `mtc/api.py`
   - Thêm hàm `decrypt_content()`
   - Cập nhật `get_chapter_content()`

## Tài liệu chi tiết

- 📖 [DECRYPTION_GUIDE.md](DECRYPTION_GUIDE.md) - Hướng dẫn tổng hợp
- 🔍 [MITMPROXY_GUIDE.md](MITMPROXY_GUIDE.md) - Chi tiết về mitmproxy
- 🔧 [DART_DECOMPILE_GUIDE.md](DART_DECOMPILE_GUIDE.md) - Chi tiết về decompile

## Lưu ý

⚠️ **Quan trọng**: Tất cả các công cụ và hướng dẫn chỉ dùng cho mục đích nghiên cứu và học tập cá nhân. Không sử dụng cho mục đích thương mại hoặc vi phạm bản quyền.

## Kết quả đã đạt được

✅ Tìm được API endpoint: `https://api.lonoapp.net/api`  
✅ Xác định được format mã hóa: Laravel AES-256-CBC  
✅ Tìm được domain chính: `truyen.onl`  
✅ Phát hiện chapter ID thấp (1-1000) không bị mã hóa  
✅ Tạo đầy đủ công cụ phân tích và hướng dẫn  

❌ Chưa tìm được APP_KEY (cần thực hiện một trong 4 phương án trên)

## Hỗ trợ

Nếu gặp vấn đề, xem phần **Troubleshooting** trong [DECRYPTION_GUIDE.md](DECRYPTION_GUIDE.md)
