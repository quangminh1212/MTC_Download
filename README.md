# Trình Tải Truyện MTC Downloader

Công cụ tải truyện chữ từ metruyencv.info và chuyển đổi sang định dạng EPUB.

## Cài đặt

### Cách 1: Sử dụng tập lệnh tự động

1. Tải về và giải nén dự án
2. Chạy file `setup.bat` bằng cách nhấp đúp vào nó
3. Làm theo các hướng dẫn trên màn hình

### Cách 2: Cài đặt thủ công

1. Cài đặt Python 3.x từ [python.org](https://www.python.org/downloads/)
2. Cài đặt các gói Python cần thiết:
   ```
   pip install httpx beautifulsoup4 ebooklib async-lru backoff playwright pytesseract Pillow appdirs tqdm lxml
   ```
3. Cài đặt trình duyệt cho Playwright:
   ```
   python -m playwright install firefox
   ```
4. Tải và cài đặt Tesseract OCR từ [đây](https://github.com/UB-Mannheim/tesseract/wiki)
   - Trong quá trình cài đặt, chọn ngôn ngữ Vietnamese
   - Cài đặt vào thư mục `Tesseract-OCR` trong thư mục dự án

## Cách sử dụng

1. Chạy chương trình:
   ```
   python main.py
   ```
   
2. Lần đầu tiên chạy, bạn cần nhập:
   - Email/tên người dùng cho metruyencv
   - Mật khẩu
   - Ổ đĩa để lưu truyện (C hoặc D)
   - Số kết nối tối đa (50 là giá trị tối ưu)
   - Chọn có lưu cấu hình hay không

3. Sau đó, nhập:
   - URL của truyện (phải là từ metruyencv.info)
   - Số chương bắt đầu
   - Số chương kết thúc

4. File EPUB sẽ được lưu vào thư mục `C:/novel/[tên-truyện]` hoặc `D:/novel/[tên-truyện]` tùy thuộc vào cấu hình của bạn.

## Xử lý sự cố

1. **Lỗi EOFError**: Nếu gặp lỗi này, hãy chạy chương trình trong Command Prompt thông thường thay vì PowerShell.

2. **Không tìm thấy Tesseract**: Đảm bảo Tesseract được cài đặt đúng vị trí hoặc cập nhật đường dẫn trong file main.py:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'đường_dẫn_đến_tesseract.exe'
   ```

3. **Lỗi URL**: Đảm bảo sử dụng URL từ metruyencv.info (không phải .com hoặc .biz)

## Lưu ý

- Chương trình yêu cầu tài khoản metruyencv để tải các chương VIP
- Đảm bảo bạn có kết nối internet ổn định khi sử dụng
- Việc tải truyện có thể mất nhiều thời gian tùy thuộc vào số lượng chương và tốc độ mạng
