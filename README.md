# MeTruyenCV Downloader

Tải truyện chữ từ metruyencv.info dưới dạng file EPUB

**⚠️ LƯU Ý QUAN TRỌNG**: Tool chỉ hỗ trợ URL từ `metruyencv.info`, không phải `metruyencv.com`. Hãy đổi URL từ `.com` sang `.info` trước khi sử dụng.

## 🚀 Cài đặt nhanh

### Cách 1: Tự động (Khuyến nghị)
1. Chạy `setup.bat` để tự động cài đặt tất cả dependencies
2. Chạy `run.bat` để khởi động ứng dụng

### Cách 2: Thủ công
1. Cài đặt Python 3.8+ từ https://python.org
2. Cài đặt dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install firefox
   ```
3. Tải và cài đặt Tesseract-OCR từ: https://github.com/UB-Mannheim/tesseract/wiki
4. Copy thư mục `Tesseract-OCR` vào thư mục dự án

## 📋 Dependencies đã được cài đặt sẵn
- httpx, beautifulsoup4, ebooklib, tqdm, backoff
- playwright, pytesseract, Pillow, appdirs, async-lru, lxml

## 🎯 Cách sử dụng

### Chạy ứng dụng
- **Phiên bản cơ bản**: `python main.py`
- **Phiên bản nhanh**: `python fast.py`
- **Hoặc sử dụng**: `run.bat`

### Kiểm tra cài đặt
- Chạy `python check_dependencies.py` để kiểm tra tất cả dependencies
- Chạy `python test_simple.py` để test import cơ bản

## 📁 Cấu trúc dự án
- `main.py` - Phiên bản cơ bản, ổn định
- `fast.py` - Phiên bản tối ưu tốc độ
- `user-agent` - Module tạo user agent ngẫu nhiên
- `requirements.txt` - Danh sách dependencies
- `setup.bat` - Script cài đặt tự động
- `run.bat` - Script chạy ứng dụng
- `check_dependencies.py` - Kiểm tra dependencies
- `HUONG_DAN.md` - Hướng dẫn chi tiết

## 🔧 Khắc phục sự cố
Xem file `HUONG_DAN.md` để biết hướng dẫn chi tiết về khắc phục sự cố.
