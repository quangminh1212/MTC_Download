# MTC Downloader

MTC Downloader là công cụ tải và trích xuất nội dung truyện từ trang MetruyenCV, giúp người dùng lưu truyện để đọc offline một cách dễ dàng.

## Tính năng

- Tải một chương truyện từ URL
- Tải nhiều chương liên tiếp
- Tải tất cả các chương của một truyện
- Trích xuất nội dung từ file HTML đã lưu
- Kết hợp nhiều chương thành một file duy nhất
- Giao diện dòng lệnh (CLI)
- Giao diện web (HTTP)
- Giao diện đồ họa (GUI)
- **Mới:** Hỗ trợ nhiều phương pháp giải mã nội dung nâng cao
  - Giải mã AES với nhiều key và chế độ khác nhau
  - Hỗ trợ định dạng mã hóa chapterData mới nhất
  - Xử lý các prefix đặc biệt (comtext, mtcontent, prp)
  - Giải mã nhiều lớp và cấu trúc dữ liệu phức tạp

## Cài đặt

### Yêu cầu

- Python 3.6 trở lên
- pip (trình quản lý gói Python)
- **Mới:** pycryptodome (cho giải mã AES)

### Cài đặt từ source

```bash
git clone https://github.com/example/mtc_downloader.git
cd mtc_downloader
pip install -e .
```

## Sử dụng

### Giao diện dòng lệnh (CLI)

#### Tải truyện

```bash
# Tải một chương
mtc-download https://metruyencv.com/truyen/ten-truyen/chuong-XX

# Tải nhiều chương liên tiếp
mtc-download https://metruyencv.com/truyen/ten-truyen/chuong-XX --num 5

# Tải tất cả các chương
mtc-download https://metruyencv.com/truyen/ten-truyen --all

# Kết hợp tất cả chương thành một file
mtc-download https://metruyencv.com/truyen/ten-truyen --all --combine

# Chỉ định thư mục đầu ra
mtc-download https://metruyencv.com/truyen/ten-truyen --all --output /path/to/folder
```

#### Trích xuất từ file HTML

```bash
# Trích xuất từ một file HTML
mtc-extract --input file.html

# Trích xuất tất cả file HTML trong thư mục
mtc-extract --input folder_with_html

# Kết hợp tất cả file thành một file duy nhất
mtc-extract --input folder_with_html --combine
```

### Giao diện web

```bash
# Khởi động ứng dụng web
mtc-web

# Chỉ định host và port
mtc-web --host 0.0.0.0 --port 8080
```

Sau khi khởi động, bạn có thể truy cập ứng dụng web tại http://localhost:3000 (hoặc port đã chỉ định).

### Giao diện đồ họa

```bash
# Khởi động ứng dụng giao diện đồ họa
mtc-gui
```

## Cấu trúc dự án

```
mtc_downloader/
├── docs/                  # Tài liệu
├── src/                   # Mã nguồn
│   └── mtc_downloader/    # Package chính
│       ├── core/          # Module cốt lõi
│       │   ├── downloader.py  # Tải truyện từ web
│       │   └── extractor.py   # Trích xuất từ HTML
│       ├── web/           # Ứng dụng web
│       │   └── app.py     # Ứng dụng Flask
│       ├── gui/           # Giao diện đồ họa
│       │   └── app.py     # Ứng dụng Tkinter
│       └── cli.py         # Giao diện dòng lệnh
├── tests/                 # Kiểm thử
│   ├── test_downloader.py # Kiểm thử tải truyện
│   └── test_enhanced_decryption.py # Kiểm thử giải mã nâng cao
├── setup.py               # Cấu hình cài đặt
└── README.md              # Tài liệu
```

## Giải mã nâng cao

Phiên bản mới nhất của MTC Downloader bao gồm nhiều cải tiến về khả năng giải mã nội dung được bảo vệ:

1. **Hỗ trợ nhiều định dạng mã hóa**
   - Base64 với bảng chuyển đổi tùy chỉnh
   - Mã hóa AES (CBC và ECB) với các khóa phổ biến
   - Mã hóa XOR với nhiều khóa khác nhau
   - Giải nén zlib sau khi giải mã

2. **Xử lý các prefix đặc biệt**
   - Định dạng "comtext" (base64 phân đoạn)
   - Định dạng "mtcontent" (nhiều lớp mã hóa)
   - Định dạng "prp" (base64 với dấu phân cách)
   - Định dạng "chapterData" (mã hóa JavaScript)

3. **Cấu trúc dữ liệu phức tạp**
   - Trích xuất từ biến JavaScript
   - Giải mã từ đối tượng JSON
   - Phân tích cấu trúc dữ liệu đặc biệt
   - Kết hợp các phần mã hóa riêng lẻ

## Đóng góp

Các đóng góp luôn được chào đón! Vui lòng tạo issue hoặc pull request trên GitHub.

## Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết. 