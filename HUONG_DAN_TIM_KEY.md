# HƯỚNG DẪN TÌM APP_KEY

## Tình hình hiện tại:

✓ Đã giải nén APK thành công
✓ Đã phân tích cấu trúc mã hóa: Laravel AES-256-CBC
✓ Đã tìm được 5 key tiềm năng trong libapp.so
✗ Các key tìm được KHÔNG hoạt động

## Phương pháp khuyến nghị: SỬ DỤNG MITMPROXY

### Cách 1: Tự động (Khuyến nghị)

```bash
# Chạy script tự động
SIMPLE_RUN.bat

# Hoặc script đầy đủ
RUN_THIS.bat
```

Script sẽ:
1. Cấu hình proxy cho BlueStacks
2. Khởi động mitmproxy
3. Tự động theo dõi traffic
4. Tìm APP_KEY khi bạn đọc chương

### Cách 2: Thủ công

**Bước 1: Khởi động mitmproxy**
```bash
mitmweb --listen-host 0.0.0.0 --listen-port 8080 --web-host 127.0.0.1 --web-port 8081
```

**Bước 2: Cấu hình BlueStacks**
```bash
# Lấy IP máy
ipconfig

# Set proxy cho BlueStacks
adb -s 127.0.0.1:5555 shell settings put global http_proxy <YOUR_IP>:8080
```

**Bước 3: Mở app và đọc chương**
- Mở app MTC/NovelFever trong BlueStacks
- Đọc bất kỳ chương nào
- Xem traffic tại: http://127.0.0.1:8081

**Bước 4: Tìm key trong traffic**
Tìm request đến:
- `https://android.lonoapp.net/api/chapters/{id}`
- `https://api.lonoapp.net/api/chapters/{id}`

Kiểm tra:
- Request headers (tìm `X-App-Key`, `Authorization`, `X-Encryption-Key`)
- Response headers
- Request/Response body

### Cách 3: Decompile với JADX

```bash
# Nếu có jadx
jadx MTC.apk -d decompiled

# Tìm trong code Java
grep -r "APP_KEY\|app_key\|encryption" decompiled/
grep -r "base64:" decompiled/
```

### Cách 4: Phân tích Flutter

```bash
# Extract Flutter snapshot
python extract_dart_snapshot.py

# Analyze strings
strings extract/lib/arm64-v8a/libapp.so | grep -i "key\|base64"
```

## Tại sao các key tìm được không hoạt động?

1. **Key có thể được obfuscate**: App có thể mã hóa/che giấu key
2. **Key động**: Key có thể được tạo động từ device ID hoặc user session
3. **Key từ server**: App có thể lấy key từ server khi khởi động
4. **Multi-layer encryption**: Có thể có nhiều lớp mã hóa

## Giải pháp thay thế

### Option 1: Bỏ qua giải mã
Nếu app tự giải mã nội dung trước khi hiển thị, có thể:
- Hook vào hàm decrypt của app
- Lấy nội dung đã giải mã trực tiếp

### Option 2: Reverse engineering sâu hơn
- Sử dụng Frida để hook các hàm crypto
- Debug app với Android Studio
- Phân tích native code với IDA Pro/Ghidra

## Kết luận

**PHƯƠNG PHÁP TỐT NHẤT**: Chạy `SIMPLE_RUN.bat` và đọc chương trong app.
Script sẽ tự động bắt key từ traffic.

Nếu không có BlueStacks, cần:
1. Cài Android emulator khác (Genymotion, Android Studio AVD)
2. Hoặc dùng thiết bị Android thật
3. Cấu hình proxy và certificate
4. Chạy mitmproxy để bắt traffic
