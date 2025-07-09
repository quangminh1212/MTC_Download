# MeTruyenCV Downloader

Công cụ tải truyện từ MeTruyenCV.com sử dụng Selenium với giao diện đơn giản.

## 🚀 Cách sử dụng nhanh

1. **Cài đặt Python 3.7+** trên máy tính
2. **Chạy file `run.bat`** - sẽ tự động cài đặt dependencies và bắt đầu
3. **Cấu hình trong `config.json`** (xem bên dưới)
4. **Theo dõi tiến trình** trong terminal

## 📁 Cấu trúc dự án

```
MTC_Download/
├── metruyencv_downloader.py    # File chính - logic tải truyện
├── config.json                # Cấu hình tài khoản và truyện cần tải
├── run.bat                     # File khởi động (Windows)
├── README.md                   # Hướng dẫn này
├── HUONG_DAN.txt              # Hướng dẫn chi tiết tiếng Việt
└── downloads/                  # Thư mục chứa truyện đã tải
    └── Tên_Truyện/            # Mỗi truyện một thư mục riêng
        ├── Chương 1.txt
        ├── Chương 2.txt
        └── ...
```

## ⚙️ Cấu hình config.json

```json
{
  "account": {
    "username": "email@gmail.com",
    "password": "your_password",
    "note": "Thông tin đăng nhập MeTruyenCV"
  },
  "download": {
    "story_url": "https://metruyencv.com/truyen/ten-truyen",
    "start_chapter": 1,
    "end_chapter": 10,
    "output_folder": "downloads",
    "note": "URL truyện và phạm vi chương (end_chapter = -1 để tải hết)"
  },
  "settings": {
    "delay_between_chapters": 2,
    "max_retries": 3,
    "headless": false,
    "browser": "auto",
    "note": "Cấu hình: delay (giây), thử lại, headless, browser"
  }
}
```

## 🔧 Tùy chọn trình duyệt

- `"auto"` - Tự động chọn (Edge → Firefox → Chrome → Brave)
- `"edge"` - Microsoft Edge
- `"firefox"` - Mozilla Firefox  
- `"chrome"` - Google Chrome
- `"brave"` - Brave Browser

## ✨ Tính năng

- ✅ **Đăng nhập tự động** với tài khoản MeTruyenCV
- ✅ **Tải nhiều chương** theo phạm vi cấu hình
- ✅ **Tự động tạo thư mục** theo tên truyện
- ✅ **Mỗi chương một file .txt** riêng biệt
- ✅ **Sử dụng Selenium** để xử lý JavaScript động
- ✅ **Tự động chọn trình duyệt** phù hợp
- ✅ **Hiển thị trình duyệt** (không headless) để theo dõi

## 📖 Ví dụ sử dụng

1. **Sửa config.json:**
   ```json
   {
     "account": {
       "username": "your_email@gmail.com",
       "password": "your_password"
     },
     "download": {
       "story_url": "https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong",
       "start_chapter": 1,
       "end_chapter": 50
     }
   }
   ```

2. **Chạy:** Double-click `run.bat`

3. **Kết quả:** Truyện sẽ được lưu trong `downloads/Tận_Thế_Chi_Siêu_Thị_Hệ_Thống/`

## ⚠️ Lưu ý

- Trình duyệt sẽ hiển thị khi tải (không chạy ẩn)
- Nội dung có thể vẫn bị mã hóa (đang nghiên cứu giải pháp)
- Nhấn `Ctrl+C` để dừng quá trình tải
- Cần tài khoản MeTruyenCV để tải một số truyện

## 🛠️ Yêu cầu hệ thống

- Windows 10/11
- Python 3.7+
- Một trong các trình duyệt: Edge, Firefox, Chrome, Brave
- Kết nối internet ổn định

## 📞 Hỗ trợ

Nếu gặp lỗi, hãy kiểm tra:
1. Python đã được cài đặt chưa
2. Trình duyệt có hoạt động không
3. Thông tin đăng nhập trong config.json có đúng không
4. Kết nối internet có ổn định không
