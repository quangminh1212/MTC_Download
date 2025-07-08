# Changelog

Tất cả các thay đổi quan trọng của project sẽ được ghi lại trong file này.

## [1.0.0] - 2025-07-08

### ✨ Tính năng mới
- 🚀 **Phiên bản đầu tiên** của MeTruyenCV Downloader
- 📚 **Tải truyện hàng loạt** từ MeTruyenCV.com
- 📖 **Chuyển đổi từng chương** thành file TXT riêng biệt
- 📦 **Tự động đóng gói** thành file ZIP
- 🎯 **Chọn phạm vi chương** cần tải
- 📊 **Hiển thị tiến trình** tải real-time
- 🌐 **Giao diện web** thân thiện và responsive

### 🛠️ Công nghệ sử dụng
- **Backend:** Python Flask
- **Web Scraping:** BeautifulSoup4, Requests
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **File Processing:** Python built-in libraries

### 📁 Cấu trúc project
```
MTC_Download/
├── app.py                 # Ứng dụng chính
├── demo_offline.py        # Demo với dữ liệu mẫu
├── requirements.txt       # Python dependencies
├── config.json           # File cấu hình
├── start_app.bat         # Script khởi động (Windows)
├── start_demo.bat        # Script khởi động demo (Windows)
├── templates/
│   ├── index.html        # Giao diện chính
│   └── demo.html         # Giao diện demo
├── downloads/            # Thư mục chứa file đã tải
├── test_downloader.py    # Script test
├── simple_test.py        # Test đơn giản
├── README.md             # Hướng dẫn sử dụng
└── CHANGELOG.md          # File này
```

### 🎯 Tính năng chính
1. **Tải truyện từ MeTruyenCV.com:**
   - Hỗ trợ tất cả truyện trên website
   - Tự động phát hiện danh sách chương
   - Lấy thông tin truyện (tên, tác giả)

2. **Xử lý nội dung:**
   - Tự động làm sạch nội dung
   - Loại bỏ quảng cáo và link spam
   - Định dạng text dễ đọc

3. **Tùy chọn tải:**
   - Chọn phạm vi chương (từ X đến Y)
   - Tải tất cả chương hoặc một phần
   - Hiển thị tiến trình real-time

4. **Xuất file:**
   - Mỗi chương = 1 file TXT
   - Tự động đóng gói thành ZIP
   - Tên file có định dạng rõ ràng

### 🚨 Lưu ý quan trọng
- ⚖️ **Chỉ sử dụng cho mục đích cá nhân và học tập**
- 📚 **Tôn trọng bản quyền** của tác giả và nhà xuất bản
- 🚫 **Không sử dụng cho mục đích thương mại**
- 💝 **Hỗ trợ tác giả** bằng cách đọc truyện trên trang chính thức

### 🐛 Vấn đề đã biết
- Một số chương có thể bị khóa hoặc yêu cầu đăng nhập
- Tốc độ tải phụ thuộc vào kết nối mạng
- Website có thể thay đổi cấu trúc HTML

### 🔮 Kế hoạch tương lai
- [ ] Hỗ trợ thêm các website truyện khác
- [ ] Tùy chọn định dạng xuất (PDF, EPUB)
- [ ] Giao diện desktop (Tkinter/PyQt)
- [ ] Tính năng đồng bộ và backup
- [ ] Hỗ trợ đa ngôn ngữ

---

## Cách đọc version
- **Major.Minor.Patch** (ví dụ: 1.0.0)
- **Major:** Thay đổi lớn, không tương thích ngược
- **Minor:** Tính năng mới, tương thích ngược
- **Patch:** Sửa lỗi, cải thiện nhỏ
