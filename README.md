# 📚 MeTruyenCV Downloader

Ứng dụng web localhost để tải truyện hàng loạt từ MeTruyenCV.com và chuyển đổi thành file TXT theo từng chương.

## ✨ Tính năng

- 📚 **Tải truyện hàng loạt** từ MeTruyenCV.com
- 📖 **Chuyển đổi từng chương** thành file TXT riêng biệt
- 📦 **Tự động đóng gói** thành file ZIP để dễ dàng tải về
- 🎯 **Chọn phạm vi chương** cần tải (từ chương X đến chương Y)
- 📊 **Hiển thị tiến trình** tải real-time với thanh progress
- 🌐 **Giao diện web thân thiện** dễ sử dụng
- 🔄 **Tự động làm sạch** nội dung (loại bỏ quảng cáo, link spam)

## 🚀 Khởi chạy nhanh

### Cách 1: File batch đơn giản (Khuyến nghị)
```bash
# Double-click file này
start.bat
```

### Cách 2: File batch đầy đủ
```bash
# Double-click file này (tiếng Việt)
run.bat

# Hoặc file này (tiếng Anh)
run_en.bat
```

### Cách 3: Chạy thủ công
```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Chạy ứng dụng
python app.py

# Truy cập: http://localhost:5000
```

## 📖 Hướng dẫn sử dụng

### Bước 1: Lấy URL truyện
1. Truy cập **MeTruyenCV.com** và tìm truyện muốn tải
2. Copy URL của trang truyện (không phải trang chương)
   - ✅ Đúng: `https://metruyencv.com/truyen/no-le-bong-toi`
   - ❌ Sai: `https://metruyencv.com/truyen/no-le-bong-toi/chuong-1`

### Bước 2: Sử dụng ứng dụng
1. Dán URL vào ô "URL Truyện"
2. Chọn phạm vi chương (ví dụ: 1-50, 1-100)
3. Nhấn "Bắt đầu tải"
4. Chờ hoàn thành và tải file ZIP

## 📁 Kết quả

File ZIP sẽ chứa các file TXT theo định dạng:
```
TenTruyen.zip
├── Chuong_001_Tieu_de_chuong.txt
├── Chuong_002_Tieu_de_chuong.txt
└── ...
```

## ⚠️ Lưu ý quan trọng

- ✅ **Chỉ sử dụng cho mục đích cá nhân và học tập**
- ✅ **Tôn trọng bản quyền** của tác giả và nhà xuất bản
- ❌ **Không sử dụng cho mục đích thương mại**
- 💝 **Hỗ trợ tác giả** bằng cách đọc truyện trên trang chính thức

## 🔧 Xử lý sự cố

### Lỗi encoding khi chạy .bat file:
**Triệu chứng:** Thấy lỗi như `'được' is not recognized as an internal or external command`
**Giải pháp:**
1. Sử dụng `start.bat` (đơn giản nhất)
2. Hoặc sử dụng `run_en.bat` (tiếng Anh)
3. Hoặc chạy từ Command Prompt thay vì PowerShell

### Lỗi "Python chưa cài đặt":
1. Tải Python từ https://python.org/downloads/
2. Tick "Add Python to PATH" khi cài đặt
3. Restart máy tính

### Lỗi "Không kết nối được":
1. Kiểm tra kết nối internet
2. Thử truy cập MeTruyenCV.com bằng trình duyệt
3. Tắt tạm thời antivirus/firewall

### Lỗi "Không tải được chương":
- Một số chương có thể bị khóa hoặc yêu cầu đăng nhập
- Kiểm tra URL có đúng định dạng không
- Thử lại với truyện khác
