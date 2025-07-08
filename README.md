# 📚 MeTruyenCV Downloader

Công cụ tải truyện từ MeTruyenCV với quản lý cấu hình thông minh.

## 🚀 Cách sử dụng

### **Chạy chương trình:**
```bash
run.bat
```

Script sẽ tự động:
- ✅ Tạo file `config.txt` nếu chưa có
- ✅ Hỏi thông tin đăng nhập lần đầu
- ✅ Lưu cài đặt để không cần nhập lại
- ✅ **Nhớ novel cuối cùng** - Gợi ý URL và chapter range
- ✅ **AUTO RUN MODE** - Tự động tiếp tục novel mà không cần input
- ✅ Tự động xử lý redirect (.com → .biz)
- ✅ Tải chapters và tạo file EPUB

## ⚙️ Cấu hình

Chỉnh sửa file `config.txt` để thay đổi cài đặt:

```ini
[LOGIN]
email=your_email@example.com
password=your_password

[DOWNLOAD]
drive=C
folder=novel
max_connections=50

[LAST_NOVEL]
url=https://metruyencv.biz/truyen/example
start_chapter=1
end_chapter=10

[SETTINGS]
auto_save=true
headless=true
chapter_timeout=30
retry_attempts=3
remember_last_novel=true
auto_run=true

[ADVANCED]
user_agent=
request_delay=1
use_ocr=true
```

## 📁 Files

```
MTC_Download/
├── run.bat              # Script chính
├── main_config.py       # Script chính với config management
├── config.txt           # File cấu hình (tự động tạo)
├── config_manager.py    # Class quản lý cấu hình
├── setup.bat            # Script cài đặt dependencies
└── README.md            # File này
```

## 🎯 Tính năng

- ✅ **Khắc phục redirect** từ .com sang .biz
- ✅ **Quản lý cấu hình** qua file config.txt
- ✅ **Smart defaults** - Nhớ novel và chapter range cuối cùng
- ✅ **AUTO RUN MODE** - Chạy hoàn toàn tự động không cần input
- ✅ **Selenium stable** thay vì Playwright
- ✅ **User-friendly** với progress bars và emoji
- ✅ **UTF-8 support** cho tiếng Việt

## 🐛 Troubleshooting

- **Lỗi driver**: Đảm bảo Firefox hoặc Chrome đã cài đặt
- **Lỗi encoding**: Script tự động xử lý UTF-8
- **Lỗi redirect**: Script tự động xử lý .com → .biz
- **Lỗi timeout**: Tăng `chapter_timeout` trong config.txt

---

**🎉 Chỉ cần chạy `run.bat` và enjoy!**
