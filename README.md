# MeTruyenCV Downloader

Công cụ tải truyện từ trang web metruyencv.com và lưu thành file txt theo từng chương sử dụng Selenium và XPath.

## Tính năng

- ✅ Tải truyện từ metruyencv.com
- ✅ Lưu từng chương thành file txt riêng biệt
- ✅ Tự động tạo thư mục theo tên truyện
- ✅ Hỗ trợ tải theo phạm vi chương
- ✅ Chạy ở chế độ headless hoặc hiển thị browser
- ✅ Xử lý lỗi và retry
- ✅ Logging chi tiết

## Cài đặt

### 1. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Cài đặt Chrome browser

Đảm bảo bạn đã cài đặt Google Chrome trên máy tính.

## Sử dụng

### Cách 1: Sử dụng script tương tác

```bash
python run_downloader.py
```

Script sẽ hỏi bạn:
- URL truyện cần tải
- Chương bắt đầu (mặc định 1)
- Chương kết thúc (để trống để tải hết)
- Có chạy ẩn browser không

### Cách 2: Sử dụng trực tiếp

```python
from metruyencv_downloader import MeTruyenCVDownloader

# Tạo downloader
downloader = MeTruyenCVDownloader(headless=True)

# Tải truyện
story_url = "https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong"
downloader.download_story(story_url, start_chapter=1, end_chapter=10)

# Đóng browser
downloader.close()
```

### Cách 3: Chỉnh sửa file main

Mở file `metruyencv_downloader.py` và chỉnh sửa hàm `main()`:

```python
def main():
    story_url = "URL_TRUYEN_CUA_BAN"
    downloader = MeTruyenCVDownloader(headless=True)
    
    try:
        # Tải 10 chương đầu
        downloader.download_story(story_url, start_chapter=1, end_chapter=10)
        
        # Hoặc tải toàn bộ truyện
        # downloader.download_story(story_url)
    finally:
        downloader.close()
```

Sau đó chạy:
```bash
python metruyencv_downloader.py
```

## Cấu trúc thư mục output

```
truyen/
└── Ten_Truyen/
    ├── Chuong_1_Ten_Chuong.txt
    ├── Chuong_2_Ten_Chuong.txt
    └── ...
```

## Cấu hình

Chỉnh sửa file `config.py` để thay đổi:
- Thời gian delay giữa các lần tải
- XPath selectors
- Chrome options
- Thư mục output

## XPath Selectors được sử dụng

- **Tên truyện**: `//h1[contains(@class, 'title')]`
- **Tác giả**: `//a[contains(@href, '/tac-gia/')]`
- **Danh sách chương**: `//a[contains(@href, '/chuong-')]`
- **Nội dung chương**: `//div[@id='chapter-content']` hoặc `//div[contains(@class, 'chapter-content')]`

## Lưu ý

1. **Tốc độ tải**: Có delay 1 giây giữa các chương để tránh bị chặn
2. **Headless mode**: Mặc định chạy ẩn browser, có thể tắt để debug
3. **Xử lý lỗi**: Tự động retry và bỏ qua chương lỗi
4. **Tên file**: Tự động làm sạch tên file để tránh ký tự không hợp lệ

## Troubleshooting

### Lỗi ChromeDriver
```
WebDriverException: 'chromedriver' executable needs to be in PATH
```
**Giải pháp**: Script tự động tải ChromeDriver, đảm bảo có kết nối internet.

### Lỗi không tìm thấy element
```
NoSuchElementException: Unable to locate element
```
**Giải pháp**: 
1. Kiểm tra XPath selectors trong `config.py`
2. Chạy ở chế độ không headless để debug
3. Trang web có thể đã thay đổi cấu trúc

### Lỗi timeout
```
TimeoutException: Message: 
```
**Giải pháp**: Tăng giá trị `TIMEOUT` trong `config.py`

## Ví dụ sử dụng

```python
# Tải 5 chương đầu
downloader.download_story(
    "https://metruyencv.com/truyen/ten-truyen", 
    start_chapter=1, 
    end_chapter=5
)

# Tải từ chương 10 đến 20
downloader.download_story(
    "https://metruyencv.com/truyen/ten-truyen", 
    start_chapter=10, 
    end_chapter=20
)

# Tải toàn bộ truyện
downloader.download_story("https://metruyencv.com/truyen/ten-truyen")
```

## License

MIT License

## Disclaimer

Công cụ này chỉ dành cho mục đích học tập và sử dụng cá nhân. Vui lòng tôn trọng bản quyền của tác giả và trang web.
