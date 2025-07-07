# Công Cụ Trích Xuất Nội Dung Truyện từ HTML

Đây là bộ công cụ giúp trích xuất nội dung truyện từ các file HTML đã lưu hoặc trực tiếp từ trang MetruyenCV và chuyển đổi thành file văn bản thuần túy để đọc dễ dàng hơn.

## Yêu cầu hệ thống

- Python 3.6 trở lên
- Thư viện BeautifulSoup4 (`pip install beautifulsoup4`)
- Thư viện Requests (`pip install requests`)
- Tkinter (thường đã được cài đặt sẵn với Python)

## Các script có sẵn

1. **extract_story.py**: Script đơn giản để trích xuất nội dung từ một file HTML.
2. **extract_story_batch.py**: Script nâng cao, hỗ trợ xử lý nhiều file HTML cùng lúc và kết hợp tất cả vào một file lớn.
3. **download_story.py**: Script để tải truyện trực tiếp từ trang web MetruyenCV.
4. **main.py**: Ứng dụng giao diện đồ họa tích hợp tất cả các tính năng trên.

## Cách sử dụng

### Sử dụng giao diện đồ họa (Đề xuất)

Cách dễ dàng nhất là chạy ứng dụng giao diện đồ họa:

```bash
python main.py
```

Ứng dụng có 4 tab với các chức năng khác nhau:

1. **Tab "Trích xuất một file"**: Trích xuất nội dung từ một file HTML đã lưu trên máy.
2. **Tab "Trích xuất nhiều file"**: Trích xuất nội dung từ nhiều file HTML trong một thư mục.
3. **Tab "Tải từ MetruyenCV"**: Tải truyện trực tiếp từ trang web MetruyenCV và lưu thành file text.
4. **Tab "Xem file đã trích xuất"**: Xem nội dung các file text đã được trích xuất.

### Tải truyện từ trang web MetruyenCV

Bạn có thể tải truyện trực tiếp từ trang web MetruyenCV sử dụng script `download_story.py`:

```bash
# Tải một chương
python download_story.py https://metruyencv.com/truyen/ten-truyen/chuong-XX

# Tải nhiều chương liên tiếp
python download_story.py https://metruyencv.com/truyen/ten-truyen/chuong-XX --num 5

# Tải tất cả chương của một truyện
python download_story.py https://metruyencv.com/truyen/ten-truyen --all

# Kết hợp tất cả các chương thành một file
python download_story.py https://metruyencv.com/truyen/ten-truyen --all --combine

# Chỉ định thư mục đầu ra
python download_story.py https://metruyencv.com/truyen/ten-truyen --all --output /path/to/folder
```

### Trích xuất từ một file HTML duy nhất

```bash
python extract_story.py
```

Script này sẽ tự động trích xuất nội dung từ file "Trinh Quan Hiền Vương - Chương 141.html" và lưu thành "Trinh Quan Hiền Vương - Chương 141.txt" trong cùng thư mục.

### Trích xuất nhiều file HTML (nâng cao)

```bash
# Trích xuất tất cả file HTML trong một thư mục
python extract_story_batch.py -i "thư/mục/chứa/html"

# Trích xuất và lưu vào thư mục khác
python extract_story_batch.py -i "thư/mục/chứa/html" -o "thư/mục/đầu/ra"

# Trích xuất và kết hợp thành một file duy nhất
python extract_story_batch.py -i "thư/mục/chứa/html" -c
```

## Lưu ý khi sử dụng

1. Khi tải truyện từ web, công cụ sẽ tự động thêm độ trễ giữa các request để tránh bị chặn.
2. Nếu tải quá nhiều chương cùng lúc, có thể gặp lỗi do trang web chặn request. Nên tăng độ trễ hoặc tải ít chương hơn.
3. Trích xuất từ file HTML đã lưu sẽ nhanh hơn và ổn định hơn so với tải trực tiếp từ web.

## Các tùy chọn của extract_story_batch.py

- `-i, --input`: Đường dẫn đến file HTML hoặc thư mục chứa các file HTML
- `-o, --output`: Đường dẫn file text đầu ra hoặc thư mục chứa các file text đầu ra
- `-c, --combine`: Kết hợp tất cả các file thành một file duy nhất

## Lưu ý

- Script sẽ tự động loại bỏ các nội dung quảng cáo trong truyện.
- Nếu không tìm thấy nội dung truyện trong file HTML, script sẽ thông báo lỗi. 