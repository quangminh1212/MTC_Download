# 🚀 HƯỚNG DẪN CẤU HÌNH BLUESTACKS - CHI TIẾT

## ✅ Thông tin cấu hình của bạn:
- **IP máy tính**: `192.168.1.113`
- **Port**: `8080`
- **mitmproxy web**: http://127.0.0.1:8081

---

## 📋 BƯỚC 1: Cấu hình Proxy trong BlueStacks

### Cách 1: Qua Settings (Khuyến nghị)

1. **Mở BlueStacks**
2. Click vào biểu tượng **⚙️ Settings** (bánh răng) ở góc phải trên
3. Chọn **Network** hoặc **Advanced**
4. Tìm phần **Proxy Configuration**
5. Chọn **Manual Proxy**
6. Nhập:
   ```
   Host: 192.168.1.113
   Port: 8080
   ```
7. Click **Save**
8. **QUAN TRỌNG**: Restart BlueStacks để áp dụng

### Cách 2: Qua ADB (Nếu cách 1 không có)

Mở Command Prompt và chạy:
```bash
# Kết nối với BlueStacks
adb connect 127.0.0.1:5555

# Set proxy
adb shell settings put global http_proxy 192.168.1.113:8080
```

---

## 📋 BƯỚC 2: Cài Certificate

### 2.1. Tải Certificate

1. Trong BlueStacks, mở **Browser** (Chrome hoặc browser mặc định)
2. Truy cập: `http://mitm.it`
3. Click vào **Android**
4. Tải file certificate (`.cer` hoặc `.crt`)

### 2.2. Cài Certificate

**Cách A: Qua Settings**

1. Mở **Settings** trong BlueStacks
2. Vào **Security** → **Credentials** → **Install from storage**
3. Chọn file certificate vừa tải
4. Đặt tên: `mitmproxy`
5. Chọn **VPN and apps** (hoặc **WiFi**)

**Cách B: Qua File Manager**

1. Mở **File Manager** trong BlueStacks
2. Tìm file certificate đã tải
3. Click vào file
4. Chọn **Install**

---

## 📋 BƯỚC 3: Test Kết Nối

1. Trong BlueStacks, mở **Browser**
2. Truy cập: `http://google.com`
3. Mở mitmproxy web interface trên máy tính: http://127.0.0.1:8081
4. Bạn sẽ thấy request đến google.com trong danh sách

✅ Nếu thấy request → Proxy hoạt động!
❌ Nếu không thấy → Kiểm tra lại cấu hình

---

## 📋 BƯỚC 4: Bắt Traffic từ App MTC

1. **Mở app MTC** trong BlueStacks
2. **Đăng nhập** (nếu cần)
3. **Tìm một truyện** bất kỳ
4. **Mở và đọc một chương**
5. Quay lại mitmproxy web interface
6. Tìm request đến `api.lonoapp.net`

---

## 📋 BƯỚC 5: Script Tự Động Tìm Key

Script `auto_find_key.py` đang chạy và sẽ:
- ✅ Tự động theo dõi traffic
- ✅ Tìm APP_KEY trong headers
- ✅ Phát hiện nội dung đã giải mã
- ✅ Lưu kết quả vào file

**Bạn chỉ cần**:
1. Cấu hình proxy (bước 1-2)
2. Mở app và đọc truyện
3. Chờ script tự động tìm key

---

## ❓ Troubleshooting

### Vấn đề 1: Không kết nối được internet sau khi set proxy

**Nguyên nhân**: Proxy chưa chạy hoặc IP sai

**Giải pháp**:
- Kiểm tra IP: `192.168.1.113` đúng chưa?
- Kiểm tra mitmproxy đang chạy: http://127.0.0.1:8081
- Tắt firewall tạm thời
- Restart BlueStacks

### Vấn đề 2: Certificate error trong app

**Nguyên nhân**: Certificate chưa cài hoặc app dùng SSL pinning

**Giải pháp**:
- Cài lại certificate từ mitm.it
- Đảm bảo chọn đúng loại certificate (VPN and apps)
- Nếu vẫn lỗi → App có SSL pinning (cần Frida)

### Vấn đề 3: Không thấy traffic trong mitmproxy

**Nguyên nhân**: Proxy chưa được set đúng

**Giải pháp**:
- Kiểm tra proxy settings trong BlueStacks
- Restart BlueStacks sau khi set proxy
- Thử clear cache của app
- Test với browser trước (google.com)

### Vấn đề 4: App không mở được

**Nguyên nhân**: App phát hiện proxy/debug

**Giải pháp**:
- Thử tắt proxy, mở app, rồi bật lại
- Clear data của app
- Reinstall app

---

## 🎯 Kết Quả Mong Đợi

Sau khi làm đúng các bước, bạn sẽ thấy:

### Trường hợp 1: Tìm thấy APP_KEY
```
✅ TÌM THẤY APP_KEY!
Header: X-App-Key
Value: base64:abcd1234...

→ File: APP_KEY.txt
```

### Trường hợp 2: Nội dung đã giải mã
```
✅ TÌM THẤY NỘI DUNG ĐÃ GIẢI MÃ!
Chương 1

Thiếu niên kiếm khách...

→ File: decrypted_sample.txt
→ App tự giải mã, không cần APP_KEY!
```

### Trường hợp 3: Vẫn mã hóa
```
🔒 Nội dung bị mã hóa (Laravel encryption)
→ Cần tìm APP_KEY bằng cách khác (Frida)
```

---

## 💡 Tips

1. **Đơn giản nhất**: Làm theo đúng thứ tự bước 1-4
2. **Test trước**: Dùng browser test proxy trước khi mở app
3. **Kiên nhẫn**: Đọc 2-3 chương để đảm bảo bắt được traffic
4. **Check log**: Xem mitmproxy web interface để biết có traffic không

---

## 📞 Nếu Cần Hỗ Trợ

1. Kiểm tra file `HUONG_DAN_CAU_HINH.txt`
2. Xem log trong mitmproxy web: http://127.0.0.1:8081
3. Xem output của script `auto_find_key.py`
4. Đọc troubleshooting ở trên

---

## ⚠️ Lưu Ý Quan Trọng

- ✅ Đảm bảo máy tính và BlueStacks cùng mạng WiFi
- ✅ Tắt antivirus/firewall nếu cần
- ✅ Restart BlueStacks sau khi set proxy
- ✅ Cài certificate đúng cách
- ✅ Test với browser trước khi dùng app

---

## 🎉 Chúc Thành Công!

Sau khi tìm được APP_KEY, bạn có thể:
1. Test với: `python test_decrypt_with_key.py <key>`
2. Cập nhật vào `mtc/api.py`
3. Tải truyện không giới hạn!

---

**Thời gian ước tính**: 15-30 phút
**Độ khó**: ⭐⭐ (Trung bình)
**Tỷ lệ thành công**: 80%
