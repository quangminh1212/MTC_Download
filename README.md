# 📚 MeTruyenCV Downloader

Ứng dụng web localhost để tải truyện hàng loạt từ MeTruyenCV.com và chuyển đổi thành file TXT theo từng chương.

## ✨ Tính năng

- 📚 **Tải truyện hàng loạt** từ MeTruyenCV.com
- 📖 **Chuyển đổi từng chương** thành file TXT riêng biệt
- 📦 **Tự động đóng gói** thành file ZIP để dễ dàng tải về
- 🎯 **Chọn phạm vi chương** cần tải (từ chương X đến chương Y)
- 📊 **Hiển thị tiến trình** tải real-time với thanh progress
- 🌐 **Giao diện web thân thiện** dễ sử dụng
- 🚀 **Chạy localhost** không cần internet sau khi cài đặt
- 🔄 **Tự động làm sạch** nội dung (loại bỏ quảng cáo, link spam)

## 🚀 Cài đặt nhanh

### Phương pháp 1: Chạy trực tiếp

1. **Tải về project:**
```bash
# Nếu có git
git clone <repository-url>
cd MTC_Download

# Hoặc tải file ZIP và giải nén
```

2. **Cài đặt Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Chạy ứng dụng chính:**
```bash
python app.py
```

4. **Mở trình duyệt và truy cập:**
```
http://localhost:5000
```

### Phương pháp 2: Chạy Demo (không cần internet)

1. **Chạy demo với dữ liệu mẫu:**
```bash
python demo_offline.py
```

2. **Truy cập demo:**
```
http://localhost:5001
```

## 📖 Hướng dẫn sử dụng chi tiết

### Bước 1: Lấy URL truyện
1. **Truy cập MeTruyenCV.com**
2. **Tìm truyện muốn tải**
3. **Copy URL từ thanh địa chỉ**
   - Ví dụ: `https://metruyencv.com/truyen/no-le-bong-toi`
   - Ví dụ: `https://metruyencv.com/truyen/cuu-vuc-kiem-de`

### Bước 2: Cấu hình tải
1. **Dán URL vào ô "URL Truyện"**
2. **Chọn phạm vi chương:**
   - **Chương bắt đầu:** Mặc định là 1
   - **Chương kết thúc:** Để trống để tải tất cả chương
   - **Ví dụ:** Từ chương 1 đến 50, từ chương 100 đến 200

### Bước 3: Bắt đầu tải
1. **Nhấn nút "Bắt đầu tải"**
2. **Theo dõi tiến trình:**
   - Thanh progress hiển thị % hoàn thành
   - Thông báo trạng thái hiện tại
   - Số chương đã tải / tổng số chương
3. **Tải file ZIP khi hoàn thành**

### Bước 4: Sử dụng file đã tải
1. **Giải nén file ZIP**
2. **Mở các file TXT bằng:**
   - Notepad, Notepad++
   - Microsoft Word
   - Bất kỳ trình đọc text nào

## Cấu trúc file đầu ra

```
downloads/
├── [Tên Truyện].zip
└── [Tên Truyện]/
    ├── Chuong_001_[Tên Chương].txt
    ├── Chuong_002_[Tên Chương].txt
    └── ...
```

## Lưu ý quan trọng

⚠️ **Chỉ sử dụng cho mục đích cá nhân và học tập**

- Tôn trọng bản quyền của tác giả và nhà xuất bản
- Không sử dụng cho mục đích thương mại
- Hỗ trợ tác giả bằng cách đọc truyện trên trang chính thức

## Khắc phục sự cố

### Lỗi không tải được chương:
- Kiểm tra URL có đúng định dạng không
- Một số chương có thể bị khóa hoặc yêu cầu đăng nhập
- Thử giảm tốc độ tải bằng cách tăng delay

### Lỗi kết nối:
- Kiểm tra kết nối internet
- Website có thể tạm thời không truy cập được
- Thử lại sau một thời gian

## Công nghệ sử dụng

- **Backend:** Python Flask
- **Web Scraping:** BeautifulSoup4, Requests
- **Frontend:** HTML, CSS, JavaScript
- **File Processing:** Python built-in libraries

## Đóng góp

Nếu bạn muốn đóng góp cho project:

1. Fork repository
2. Tạo branch mới cho feature
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## License

Project này chỉ dành cho mục đích học tập và sử dụng cá nhân.

## Liên hệ

Nếu có vấn đề hoặc góp ý, vui lòng tạo issue trên GitHub.
