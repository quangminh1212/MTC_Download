# MeTruyenCV Downloader

Tải truyện chữ từ metruyencv.info dưới dạng file EPUB

**⚠️ LƯU Ý QUAN TRỌNG**: Tool hỗ trợ URL từ `metruyencv.com`. Nếu bạn có URL `.info`, tool sẽ tự động chuyển đổi sang `.com`.

## 🚀 Cài đặt nhanh

### Cách 1: Tự động (Khuyến nghị)
1. Chạy `setup.bat` - Script sẽ tự động:
   - Cài đặt tất cả Python packages
   - Cài đặt Playwright browsers
   - Tải và cài đặt Tesseract-OCR
   - Kiểm tra và xác minh cài đặt
2. Chạy `run.bat` để khởi động ứng dụng

### Cách 2: Thủ công
1. Cài đặt Python 3.8+ từ https://python.org
2. Cài đặt dependencies:
   ```bash
   pip install -r requirements.txt
   python -m playwright install firefox
   ```
3. Tải và cài đặt Tesseract-OCR từ: https://github.com/UB-Mannheim/tesseract/wiki
4. Copy thư mục `Tesseract-OCR` vào thư mục dự án

## 📋 Dependencies
- httpx, beautifulsoup4, ebooklib, tqdm, backoff
- playwright, pytesseract, Pillow, appdirs, async-lru, lxml

## 🎯 Cách sử dụng

### Chạy ứng dụng
- **Phiên bản cơ bản**: `python main.py`
- **Phiên bản nhanh**: `python fast.py`
- **Hoặc sử dụng**: `run.bat`

## 📁 Cấu trúc dự án
- `main.py` - Phiên bản cơ bản, ổn định
- `fast.py` - Phiên bản tối ưu tốc độ
- `user-agent/` - Module tạo user agent ngẫu nhiên
- `requirements.txt` - Danh sách dependencies
- `setup.bat` - Script cài đặt tự động (tích hợp đầy đủ)
- `run.bat` - Script chạy ứng dụng
- `HUONG_DAN.md` - Hướng dẫn chi tiết

## 🔧 Khắc phục sự cố
- Nếu Playwright lỗi: `python -m playwright install firefox`
- Nếu Tesseract lỗi: Chạy lại `setup.bat` hoặc tải thủ công từ GitHub
- Xem file `HUONG_DAN.md` để biết hướng dẫn chi tiết
