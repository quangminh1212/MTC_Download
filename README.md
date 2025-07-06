# Trình Tải Truyện MTC Downloader

Công cụ tải truyện chữ từ metruyencv.info và chuyển đổi sang định dạng EPUB.

## Cài đặt

### Cách 1: Sử dụng các tập lệnh tự động

1. Chạy file `setup.bat` bằng cách nhấp đúp vào nó để cài đặt các gói Python cần thiết
2. Nếu bạn đã cài đặt Tesseract OCR tại vị trí khác (như `C:\Program Files\Tesseract-OCR`), hãy chạy `update-tesseract.bat` để cập nhật đường dẫn
3. Nếu chưa có gói ngôn ngữ tiếng Việt cho Tesseract OCR, hãy chạy `download-vie-lang.bat` để tải và cài đặt

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
4. Cài đặt Tesseract OCR từ [đây](https://github.com/UB-Mannheim/tesseract/wiki)
   - Trong quá trình cài đặt, chọn ngôn ngữ Vietnamese
   - Cài đặt vào thư mục `C:\Program Files\Tesseract-OCR` hoặc bất kỳ vị trí nào bạn muốn
   - Cập nhật đường dẫn Tesseract trong file `main.py` và `fast.py`:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
     ```

## Cách sử dụng

1. Sử dụng file `run-app.bat` để chạy chương trình trong Command Prompt (đề xuất)

2. Hoặc mở Command Prompt (không phải PowerShell) và chạy lệnh:
   ```
   python main.py
   ```
   
3. Lần đầu tiên chạy, bạn cần nhập:
   - Email/tên người dùng cho metruyencv
   - Mật khẩu
   - Ổ đĩa để lưu truyện (C hoặc D)
   - Số kết nối tối đa (50 là giá trị tối ưu)
   - Chọn có lưu cấu hình hay không

4. Sau đó, nhập:
   - URL của truyện (phải là từ metruyencv.info)
   - Số chương bắt đầu
   - Số chương kết thúc

5. File EPUB sẽ được lưu vào thư mục `C:/novel/[tên-truyện]` hoặc `D:/novel/[tên-truyện]` tùy thuộc vào cấu hình của bạn.

## Xử lý sự cố

1. **Lỗi EOFError**: Nếu gặp lỗi này, hãy chạy chương trình trong Command Prompt thông thường thay vì PowerShell. Sử dụng file `run-app.bat` để tránh vấn đề này.

2. **Không tìm thấy Tesseract**: Nếu Tesseract OCR được cài đặt ở vị trí khác, chạy `update-tesseract.bat` để cập nhật đường dẫn.

3. **Lỗi URL**: Đảm bảo sử dụng URL từ metruyencv.info (không phải .com hoặc .biz)

4. **Cảnh báo về ~laywright**: Chạy file `fix-laywright.bat` để xóa phân phối không hợp lệ

## Lưu ý

- Chương trình yêu cầu tài khoản metruyencv để tải các chương VIP
- Đảm bảo bạn có kết nối internet ổn định khi sử dụng
- Việc tải truyện có thể mất nhiều thời gian tùy thuộc vào số lượng chương và tốc độ mạng
