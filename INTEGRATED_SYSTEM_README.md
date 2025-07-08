# MeTruyenCV Downloader - Hệ Thống Tích Hợp

## 🚀 Cài Đặt Nhanh

### Bước 1: Chạy Setup
```bash
setup.bat
```

### Bước 2: Chạy Ứng Dụng
```bash
run.bat
```

## 📋 Tính Năng Chính

### 🖥️ Console Mode
- Chạy trực tiếp trong command line
- Sử dụng file `config.txt` để cấu hình
- Phù hợp cho automation và scripting
- Logs được lưu trong `download.log`

### 🌐 Web Interface
- Giao diện web thân thiện
- Cấu hình qua web browser
- Real-time progress tracking
- Multi-threading support
- Logs được lưu trong `web_app.log`

## 🔧 Cách Sử dụng

### Lần Đầu Sử Dụng

1. **Chạy setup.bat**
   ```bash
   setup.bat
   ```
   - Tự động cài đặt Python (nếu chưa có)
   - Tạo virtual environment
   - Cài đặt tất cả dependencies
   - Tạo shortcuts trên Desktop

2. **Chọn chế độ chạy**
   ```bash
   run.bat
   ```
   - Chọn [1] cho Console Mode
   - Chọn [2] cho Web Interface

### Console Mode

1. **Chạy trực tiếp:**
   ```bash
   run.bat
   # Chọn [1] Console Mode
   ```

2. **Hoặc dùng shortcut:**
   - Double-click "MeTruyenCV Console.lnk" trên Desktop

3. **Cấu hình:**
   - File `config.txt` sẽ được tạo tự động
   - Chỉnh sửa file này để thay đổi cấu hình

### Web Interface

1. **Chạy web server:**
   ```bash
   run.bat
   # Chọn [2] Web Interface
   ```

2. **Hoặc dùng shortcut:**
   - Double-click "MeTruyenCV Web.lnk" trên Desktop

3. **Truy cập web:**
   - Mở browser: http://localhost:5000
   - Cấu hình: http://localhost:5000/config
   - Download: http://localhost:5000/download
   - Logs: http://localhost:5000/logs

## 📁 Cấu Trúc File

```
MTC_Download/
├── run.bat                 # File chạy chính (chọn mode)
├── setup.bat              # Setup tự động toàn bộ hệ thống
├── main_config.py          # Console downloader
├── app.py                  # Web server
├── config.txt              # File cấu hình
├── requirements.txt        # Dependencies chính
├── requirements_web.txt    # Web dependencies
├── venv/                   # Virtual environment
├── templates/              # Web templates
├── static/                 # Web assets
├── download.log            # Console logs
└── web_app.log            # Web logs
```

## 🔗 Shortcuts

Sau khi chạy `setup.bat`, sẽ có 2 shortcuts trên Desktop:

- **MeTruyenCV Console.lnk**: Chạy trực tiếp Console Mode
- **MeTruyenCV Web.lnk**: Chạy trực tiếp Web Interface

## ⚙️ Cấu Hình

### Console Mode (config.txt)
```ini
[DEFAULT]
email = your_email@example.com
password = your_password
download_path = downloads
max_workers = 3
timeout = 30
```

### Web Interface
- Truy cập http://localhost:5000/config
- Cấu hình qua giao diện web
- Lưu tự động vào database

## 🔍 Troubleshooting

### Lỗi Python không tìm thấy
```bash
# Chạy lại setup với quyền Administrator
setup.bat
```

### Lỗi dependencies
```bash
# Xóa venv và chạy lại setup
rmdir /s /q venv
setup.bat
```

### Lỗi web server
```bash
# Kiểm tra port 5000 có bị chiếm không
netstat -an | findstr :5000
```

## 📝 Logs

### Console Mode
- File: `download.log`
- Format: Timestamp + Level + Message

### Web Interface  
- File: `web_app.log`
- Real-time logs tại: http://localhost:5000/logs

## 🆕 Tính Năng Mới

### Tích Hợp Hoàn Toàn
- Một file setup cho cả 2 mode
- Một file run để chọn mode
- Shortcuts tự động cho cả 2 mode

### Auto Setup
- Tự động tải và cài Python
- Tự động tạo virtual environment
- Tự động cài đặt tất cả dependencies

### User-Friendly
- Giao diện tiếng Việt
- Hướng dẫn chi tiết
- Error handling tốt hơn

## 💡 Tips

1. **Lần đầu sử dụng**: Chạy `setup.bat` với quyền Administrator
2. **Cập nhật**: Chạy lại `setup.bat` để cập nhật dependencies
3. **Backup**: Sao lưu file `config.txt` trước khi cập nhật
4. **Performance**: Web mode hỗ trợ multi-threading tốt hơn
5. **Debugging**: Kiểm tra logs để troubleshoot

## 🔄 Cập Nhật

Để cập nhật hệ thống:
```bash
# Xóa virtual environment cũ
rmdir /s /q venv

# Chạy lại setup
setup.bat
```

## 📞 Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra logs
2. Chạy lại setup.bat
3. Đảm bảo có quyền Administrator
4. Kiểm tra kết nối internet
