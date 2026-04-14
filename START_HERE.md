# 🚀 HƯỚNG DẪN NHANH - Tìm APP_KEY với BlueStacks

## ✅ Bạn đã có:
- ✅ BlueStacks đang chạy
- ✅ App NovelFever đã cài trong BlueStacks

## 🎯 Mục tiêu:
Bắt network traffic từ app để tìm APP_KEY hoặc nội dung đã giải mã

---

## 📋 CÁCH 1: Tự động (KHUYẾN NGHỊ)

### Chạy 1 lệnh duy nhất:

```bash
quick_start.bat
```

Script này sẽ:
1. ✅ Cài mitmproxy tự động
2. ✅ Hiển thị IP máy tính
3. ✅ Hướng dẫn cấu hình BlueStacks
4. ✅ Mở mitmproxy web interface
5. ✅ Sẵn sàng bắt traffic

### Sau khi chạy:

1. **Cấu hình BlueStacks** (làm 1 lần):
   - Mở Settings → Network
   - Chọn Manual Proxy
   - Host: `<IP hiển thị>` (ví dụ: 192.168.1.100)
   - Port: `8080`
   - Save và Restart BlueStacks

2. **Cài certificate** (làm 1 lần):
   - Trong BlueStacks, mở Browser
   - Vào: `http://mitm.it`
   - Tải và cài Android certificate

3. **Bắt traffic**:
   - Mở app NovelFever
   - Đọc bất kỳ chương nào
   - Xem mitmproxy web interface (http://127.0.0.1:8081)

4. **Tìm APP_KEY**:
   - Tìm request đến `api.lonoapp.net`
   - Xem Request/Response Headers
   - Tìm: `X-App-Key`, `Authorization`, hoặc nội dung đã giải mã

---

## 📋 CÁCH 2: Tự động phân tích

### Terminal 1: Chạy mitmproxy
```bash
start_mitmproxy.bat
```

### Terminal 2: Chạy auto finder
```bash
python auto_find_key.py
```

Script sẽ **TỰ ĐỘNG**:
- ✅ Theo dõi traffic
- ✅ Tìm APP_KEY trong headers
- ✅ Phát hiện nội dung đã giải mã
- ✅ Lưu kết quả vào file

### Sau đó:
- Mở app và đọc truyện
- Script sẽ tự động báo khi tìm thấy key
- Kiểm tra file `APP_KEY.txt`

---

## 📋 CÁCH 3: Thủ công (Chi tiết)

Xem hướng dẫn đầy đủ: [BLUESTACKS_SETUP.md](BLUESTACKS_SETUP.md)

---

## 🎉 Khi tìm được APP_KEY

### Test ngay:
```bash
python test_decrypt_with_key.py "base64:YOUR_KEY_HERE"
```

### Nếu thành công:
1. Mở file `mtc/api.py`
2. Thêm APP_KEY vào đầu file
3. Uncomment hàm `decrypt_content()`
4. Chạy lại downloader

---

## ❓ Troubleshooting

### Vấn đề: Không thấy traffic trong mitmproxy
**Giải pháp**:
- Kiểm tra proxy settings trong BlueStacks
- Restart BlueStacks sau khi set proxy
- Kiểm tra IP máy tính đúng chưa
- Tắt firewall tạm thời

### Vấn đề: Certificate error
**Giải pháp**:
- Cài lại certificate từ mitm.it
- App có thể dùng SSL pinning → xem phần Frida

### Vấn đề: App không kết nối được
**Giải pháp**:
- Kiểm tra mitmproxy đang chạy
- Thử clear cache của app
- Restart app

---

## 🔧 Nếu SSL Pinning

App có thể dùng SSL pinning để chặn mitmproxy. Nếu gặp vấn đề:

### Dùng Frida (xem hướng dẫn):
- [docs/MITMPROXY_GUIDE.md](docs/MITMPROXY_GUIDE.md) - Phần Frida
- [docs/DART_DECOMPILE_GUIDE.md](docs/DART_DECOMPILE_GUIDE.md)

---

## 📚 Tài liệu đầy đủ

- 📖 [BLUESTACKS_SETUP.md](BLUESTACKS_SETUP.md) - Chi tiết setup
- 📖 [docs/DECRYPTION_GUIDE.md](docs/DECRYPTION_GUIDE.md) - Tổng hợp tất cả phương án
- 📖 [docs/MITMPROXY_GUIDE.md](docs/MITMPROXY_GUIDE.md) - Hướng dẫn mitmproxy
- 📖 [docs/DART_DECOMPILE_GUIDE.md](docs/DART_DECOMPILE_GUIDE.md) - Decompile Dart

---

## 💡 Tips

1. **Đơn giản nhất**: Chạy `quick_start.bat` và làm theo hướng dẫn
2. **Tự động nhất**: Dùng `auto_find_key.py` để tự động phát hiện
3. **Nếu không được**: Xem troubleshooting hoặc thử Frida

---

## ⚠️ Lưu ý

- Chỉ dùng cho mục đích nghiên cứu cá nhân
- Không sử dụng thương mại
- Tôn trọng bản quyền

---

## 🎯 Kết quả mong đợi

Sau khi làm đúng, bạn sẽ có:

1. ✅ APP_KEY để giải mã
2. ✅ Hoặc phát hiện app đã giải mã sẵn
3. ✅ Có thể tải truyện không mã hóa

Chúc thành công! 🎉
