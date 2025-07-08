# 📚 Hướng dẫn sử dụng MeTruyenCV Downloader

## 🚀 Khởi động nhanh

### Cách 1: Sử dụng script Windows (Khuyến nghị)
```bash
# Double-click file này để chạy ứng dụng
start_app.bat
```

### Cách 2: Chạy thủ công
```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Chạy ứng dụng
python app.py

# Truy cập: http://localhost:5000
```

## 📖 Hướng dẫn từng bước

### Bước 1: Tìm truyện trên MeTruyenCV.com
1. Mở trình duyệt và truy cập **https://metruyencv.com**
2. Tìm kiếm truyện bạn muốn tải
3. Vào trang thông tin truyện (không phải trang chương)

### Bước 2: Copy URL truyện
**URL đúng** (trang thông tin truyện):
```
✅ https://metruyencv.com/truyen/no-le-bong-toi
✅ https://metruyencv.com/truyen/cuu-vuc-kiem-de
✅ https://metruyencv.com/truyen/ten-truyen-bat-ky
```

**URL sai** (trang chương):
```
❌ https://metruyencv.com/truyen/no-le-bong-toi/chuong-1
❌ https://metruyencv.com/truyen/no-le-bong-toi/chuong-100
```

### Bước 3: Sử dụng ứng dụng
1. **Mở ứng dụng:** http://localhost:5000
2. **Dán URL** vào ô "URL Truyện"
3. **Chọn phạm vi chương:**
   - Chương bắt đầu: 1 (mặc định)
   - Chương kết thúc: để trống để tải tất cả
   - Ví dụ: từ chương 1 đến 50
4. **Nhấn "Bắt đầu tải"**
5. **Chờ hoàn thành** và tải file ZIP

## 📊 Theo dõi tiến trình

Ứng dụng sẽ hiển thị:
- **Thanh tiến trình** với % hoàn thành
- **Thông báo trạng thái** hiện tại
- **Số chương** đã tải / tổng số chương
- **Danh sách chương thất bại** (nếu có)

## 📁 Kết quả

### Cấu trúc file ZIP:
```
TenTruyen.zip
├── Chuong_001_Tieu_de_chuong_1.txt
├── Chuong_002_Tieu_de_chuong_2.txt
├── Chuong_003_Tieu_de_chuong_3.txt
└── ...
```

### Nội dung file TXT:
```
Tiêu đề chương
==================================================

Nội dung chương đã được làm sạch...
```

## ⚠️ Xử lý sự cố

### Lỗi "Không thể kết nối"
**Nguyên nhân:**
- Không có internet
- Website đang bảo trì
- Bị chặn bởi firewall

**Giải pháp:**
1. Kiểm tra kết nối internet
2. Thử truy cập MeTruyenCV.com bằng trình duyệt
3. Tắt tạm thời antivirus/firewall
4. Thử lại sau vài phút

### Lỗi "Không tìm thấy chương"
**Nguyên nhân:**
- URL sai định dạng
- Chương bị khóa/xóa
- Truyện không tồn tại

**Giải pháp:**
1. Kiểm tra lại URL (phải là trang truyện, không phải trang chương)
2. Thử với truyện khác
3. Kiểm tra truyện có tồn tại trên website không

### Lỗi "Nội dung rỗng"
**Nguyên nhân:**
- Chương bị khóa (cần đăng nhập)
- Website thay đổi cấu trúc
- Chương chưa được đăng

**Giải pháp:**
1. Bỏ qua các chương bị khóa
2. Thử tải từ chương khác
3. Kiểm tra chương có nội dung trên website không

## 🎯 Mẹo sử dụng hiệu quả

### 1. Tải theo batch nhỏ
```
Thay vì tải 1000 chương một lúc:
- Tải 1-100 trước
- Sau đó tải 101-200
- Tiếp tục từng batch 100 chương
```

### 2. Kiểm tra trước khi tải
```
- Vào trang truyện kiểm tra số chương mới nhất
- Thử tải 1-2 chương đầu để test
- Nếu OK thì tải toàn bộ
```

### 3. Xử lý chương thất bại
```
- Ghi lại danh sách chương thất bại
- Tải lại từng chương riêng lẻ
- Hoặc bỏ qua nếu không quan trọng
```

## 🔧 Tùy chỉnh nâng cao

### Thay đổi cấu hình trong config.json:
```json
{
    "downloader": {
        "delay_between_chapters": 2,    // Delay giữa các chương (giây)
        "max_retries": 3,               // Số lần thử lại khi lỗi
        "timeout": 30                   // Timeout cho mỗi request (giây)
    }
}
```

### Thay đổi User-Agent:
Mở file `app.py` và tìm dòng:
```python
'User-Agent': 'Mozilla/5.0...'
```

## 📞 Hỗ trợ

### Nếu gặp vấn đề:
1. **Kiểm tra log** trong terminal/command prompt
2. **Thử với truyện khác** để xác định vấn đề
3. **Restart ứng dụng** và thử lại
4. **Kiểm tra kết nối mạng**

### Thông tin debug:
- Ứng dụng sẽ in log chi tiết trong terminal
- Theo dõi các thông báo lỗi
- Ghi lại URL và chương gây lỗi

## ⚖️ Lưu ý pháp lý

- ✅ **Sử dụng cho mục đích cá nhân và học tập**
- ✅ **Tôn trọng bản quyền** tác giả và nhà xuất bản
- ❌ **Không sử dụng cho mục đích thương mại**
- ❌ **Không phân phối lại** nội dung đã tải

## 🎉 Chúc bạn sử dụng thành công!

Ứng dụng đã sẵn sàng để tải truyện từ MeTruyenCV.com. Hãy bắt đầu với một truyện nhỏ để làm quen trước khi tải những bộ truyện dài!
