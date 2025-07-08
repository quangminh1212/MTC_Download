# Hướng dẫn sử dụng MeTruyenCV Downloader

## Mô tả
Tool này giúp tải truyện chữ từ metruyencv.info dưới dạng file EPUB.

**LƯU Ý QUAN TRỌNG**: Tool chỉ hỗ trợ URL từ `metruyencv.info`, không phải `metruyencv.com`. Hãy đổi URL từ `.com` sang `.info` trước khi sử dụng.

## Cài đặt

### Bước 1: Cài đặt Python
- Tải và cài đặt Python 3.8+ từ https://python.org
- Đảm bảo chọn "Add Python to PATH" khi cài đặt

### Bước 2: Cài đặt dependencies
Chạy file `setup.bat` hoặc thực hiện thủ công:

```bash
pip install httpx beautifulsoup4 ebooklib tqdm backoff playwright pytesseract Pillow appdirs async-lru lxml
playwright install firefox
```

### Bước 3: Cài đặt Tesseract-OCR
1. Tải Tesseract-OCR từ: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài đặt và copy thư mục `Tesseract-OCR` vào thư mục dự án này
3. Đảm bảo file `Tesseract-OCR\tesseract.exe` tồn tại

## Cách sử dụng

### Phương pháp 1: Sử dụng script
- Chạy `run.bat` và chọn phiên bản muốn sử dụng

### Phương pháp 2: Chạy trực tiếp
- **Phiên bản cơ bản**: `python main.py`
- **Phiên bản nhanh**: `python fast.py`

## Cấu hình lần đầu
Khi chạy lần đầu, bạn sẽ được yêu cầu nhập:
- Email tài khoản metruyencv
- Password
- Ổ đĩa lưu truyện (C/D)
- Số kết nối tối đa (khuyến nghị: 50)
- Có lưu cấu hình không (Y/N)

## Sử dụng
1. Nhập URL truyện từ metruyencv.info
2. Nhập chapter bắt đầu
3. Nhập chapter kết thúc
4. Chờ tool tải và tạo file EPUB

## File output
- File EPUB sẽ được lưu trong thư mục `{ổ đĩa}:/novel/{tên truyện}/`
- Ví dụ: `D:/novel/Ten Truyen/tentruyen.epub`

## Khắc phục sự cố

### Lỗi thiếu module
```bash
pip install [tên module bị thiếu]
```

### Lỗi Playwright
```bash
playwright install firefox
```

### Lỗi Tesseract
- Đảm bảo thư mục `Tesseract-OCR` có trong thư mục dự án
- Kiểm tra file `Tesseract-OCR\tesseract.exe` tồn tại

### Lỗi kết nối
- Kiểm tra kết nối internet
- Thử giảm số kết nối tối đa
- Đảm bảo URL là metruyencv.info (không phải .com)

## Tính năng
- Tải truyện từ metruyencv.info
- Hỗ trợ OCR cho các chapter có hình ảnh
- Tạo file EPUB với metadata đầy đủ
- Hỗ trợ tải song song để tăng tốc độ
- Tự động retry khi gặp lỗi
- Lưu cấu hình để sử dụng lại

## Phiên bản
- **main.py**: Phiên bản cơ bản, ổn định
- **fast.py**: Phiên bản tối ưu tốc độ, sử dụng screenshot + OCR cho chapters bị thiếu
