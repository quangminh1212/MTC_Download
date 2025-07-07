# Công Cụ Trích Xuất Nội Dung Truyện từ HTML

Đây là bộ công cụ giúp trích xuất nội dung truyện từ các file HTML đã lưu (ví dụ từ trang MetruyenCV) và chuyển đổi thành file văn bản thuần túy để đọc dễ dàng hơn.

## Yêu cầu hệ thống

- Python 3.6 trở lên
- Thư viện BeautifulSoup4 (`pip install beautifulsoup4`)

## Các script có sẵn

1. **extract_story.py**: Script đơn giản để trích xuất nội dung từ một file HTML.
2. **extract_story_batch.py**: Script nâng cao, hỗ trợ xử lý nhiều file HTML cùng lúc và kết hợp tất cả vào một file lớn.

## Cách sử dụng

### Trích xuất từ một file HTML duy nhất

```bash
python extract_story.py
```

Script này sẽ tự động trích xuất nội dung từ file "Trinh Quan Hiền Vương - Chương 141.html" và lưu thành "Trinh Quan Hiền Vương - Chương 141.txt" trong cùng thư mục.

### Trích xuất nhiều file HTML (nâng cao)

#### Trích xuất một file HTML và chỉ định đường dẫn đầu ra

```bash
python extract_story_batch.py -i "đường/dẫn/file.html" -o "đường/dẫn/file_output.txt"
```

#### Trích xuất tất cả file HTML trong thư mục

```bash
python extract_story_batch.py -i "thư/mục/chứa/html"
```

#### Trích xuất và kết hợp tất cả file HTML trong thư mục thành một file duy nhất

```bash
python extract_story_batch.py -i "thư/mục/chứa/html" -c
```

Script này sẽ tạo một file "combined_story.txt" chứa nội dung của tất cả các file HTML trong thư mục.

#### Trích xuất tất cả file HTML trong thư mục hiện tại

```bash
python extract_story_batch.py
```

## Các tùy chọn của extract_story_batch.py

- `-i, --input`: Đường dẫn đến file HTML hoặc thư mục chứa các file HTML
- `-o, --output`: Đường dẫn file text đầu ra hoặc thư mục chứa các file text đầu ra
- `-c, --combine`: Kết hợp tất cả các file thành một file duy nhất

## Lưu ý

- Script sẽ tự động loại bỏ các nội dung quảng cáo trong truyện.
- Nếu không tìm thấy nội dung truyện trong file HTML, script sẽ thông báo lỗi. 