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

1. Sử dụng file `run-app.bat` để chạy chương trình. Bạn sẽ có 2 tùy chọn:

   a. **Chạy bình thường**: Nhập thông tin trực tiếp khi chương trình chạy
   
   b. **Chạy từ file cấu hình**: Sử dụng thông tin đã được cấu hình sẵn trong file `config.txt`

2. **Cấu hình file config.txt**:
   
   Bạn có thể chỉnh sửa file `config.txt` để thiết lập sẵn các thông tin:
   ```
   # Cấu hình tài khoản
   email=your_email@example.com
   password=your_password

   # Cài đặt lưu trữ và hiệu suất
   disk=D
   max_connections=50

   # URL truyện (lưu ý phải dùng dạng metruyencv.info)
   novel_url=https://metruyencv.info/truyen/your-novel-url

   # Chọn chương cần tải
   start_chapter=1
   end_chapter=100
   ```

3. Nếu là lần đầu tiên chạy và không sử dụng file cấu hình, bạn sẽ cần nhập:
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

## Tính năng mới: Ghi nhật ký chi tiết

Phiên bản mới nhất đã thêm tính năng ghi nhật ký chi tiết để giúp theo dõi quá trình tải truyện và gỡ lỗi khi có sự cố xảy ra.

### Thông tin về hệ thống ghi log:

- Tất cả các log được lưu trong thư mục `logs` 
- Tên file log theo định dạng: `mtc_downloader_YYYYMMDD_HHMMSS.log`
- Log sẽ ghi chi tiết về tất cả các bước của quy trình tải, bao gồm:
  - Thông tin kết nối và cấu hình
  - Quá trình tải và xử lý từng chương 
  - Thời gian xử lý mỗi bước
  - Các lỗi và cảnh báo nếu có
  - Thống kê về kết quả tải

### Cách xem log:

1. Sau khi tải truyện hoàn tất, bạn có thể xem file log trong thư mục `logs`
2. Mở file log bằng bất kỳ trình soạn thảo văn bản nào (như Notepad)
3. File log được sắp xếp theo thứ tự thời gian, từ đầu quá trình tải đến kết thúc

### Lợi ích của hệ thống log:

- Giúp hiểu rõ hơn về quá trình tải truyện
- Dễ dàng phát hiện và gỡ lỗi khi có sự cố 
- Theo dõi hiệu suất và thời gian xử lý
- Hữu ích khi cần hỗ trợ kỹ thuật

### Các mức độ log:

- **INFO**: Thông tin thông thường về tiến trình
- **DEBUG**: Thông tin chi tiết, hữu ích khi gỡ lỗi
- **WARNING**: Cảnh báo về các vấn đề không nghiêm trọng
- **ERROR**: Lỗi đã xảy ra nhưng ứng dụng vẫn có thể tiếp tục
- **CRITICAL**: Lỗi nghiêm trọng khiến ứng dụng không thể tiếp tục
