# Hướng dẫn setup mitmproxy với BlueStacks

## Bước 1: Cài đặt mitmproxy

```bash
pip install mitmproxy
```

## Bước 2: Tìm IP máy tính

```bash
ipconfig
```

Tìm dòng **IPv4 Address** của mạng đang dùng (ví dụ: `192.168.1.100`)

## Bước 3: Chạy mitmproxy

```bash
mitmweb --listen-host 0.0.0.0 --listen-port 8080
```

Hoặc chạy file: `start_mitmproxy.bat`

Mở browser: http://127.0.0.1:8081

## Bước 4: Cấu hình proxy trong BlueStacks

### Cách 1: Dùng Settings (Khuyến nghị)

1. Mở **BlueStacks**
2. Click vào **Settings** (biểu tượng bánh răng)
3. Vào **Network**
4. Chọn **Manual Proxy Configuration**
5. Nhập:
   - **Proxy Host**: IP máy tính (ví dụ: `192.168.1.100`)
   - **Proxy Port**: `8080`
6. Click **Save**
7. **Restart BlueStacks**

### Cách 2: Dùng ADB (Nếu cách 1 không có)

```bash
# Kết nối với BlueStacks
adb connect 127.0.0.1:5555

# Hoặc dùng HD-Adb.exe của BlueStacks
"C:\Program Files\BlueStacks_nxt\HD-Adb.exe" connect 127.0.0.1:5555

# Set proxy
adb shell settings put global http_proxy <YOUR_IP>:8080

# Ví dụ:
adb shell settings put global http_proxy 192.168.1.100:8080
```

## Bước 5: Cài certificate trong BlueStacks

### 5.1. Tải certificate

1. Trong BlueStacks, mở **Browser**
2. Truy cập: `http://mitm.it`
3. Click **Android**
4. Tải file certificate (`.cer`)

### 5.2. Cài certificate

**Cách A: Qua Settings (Android 7+)**

1. Mở **Settings** trong BlueStacks
2. Vào **Security** → **Install from storage**
3. Chọn file certificate vừa tải
4. Đặt tên: `mitmproxy`
5. Chọn **VPN and apps**

**Cách B: Qua ADB (Nếu cách A không được)**

```bash
# Push certificate
adb push mitmproxy-ca-cert.cer /sdcard/

# Cài đặt
adb shell am start -a android.credentials.INSTALL
```

## Bước 6: Test kết nối

1. Trong BlueStacks, mở **Browser**
2. Truy cập: `http://google.com`
3. Kiểm tra mitmproxy web interface (http://127.0.0.1:8081)
4. Bạn sẽ thấy request đến google.com

## Bước 7: Bắt traffic từ app

1. Mở app **NovelFever** trong BlueStacks
2. Tìm một truyện bất kỳ
3. Mở và đọc một chương
4. Quay lại mitmproxy web interface
5. Tìm request đến `api.lonoapp.net`
6. Xem **Request Headers** và **Response**

## Bước 8: Tìm APP_KEY

### Nơi có thể tìm thấy APP_KEY:

1. **Request Headers**:
   - `X-App-Key`
   - `X-Encryption-Key`
   - `Authorization`

2. **Response Headers**:
   - `X-Key`
   - `X-Encryption-Key`

3. **Response Body**:
   - Nếu app giải mã trước khi hiển thị, bạn sẽ thấy plain text!

4. **Config endpoint**:
   - Tìm request đến `/config`, `/init`, `/bootstrap`

## Bước 9: Phân tích với script

Sau khi bắt được traffic, lưu lại:

1. Trong mitmproxy, click **File** → **Save**
2. Lưu thành `traffic.flow`
3. Chạy script phân tích:

```bash
python analyze_mitmproxy_traffic.py traffic.flow
```

## Troubleshooting

### Vấn đề 1: BlueStacks không kết nối được internet sau khi set proxy

**Giải pháp**:
- Kiểm tra IP máy tính đúng chưa
- Kiểm tra mitmproxy đang chạy chưa
- Tắt firewall tạm thời
- Restart BlueStacks

### Vấn đề 2: Certificate error trong app

**Giải pháp**:
- App có thể dùng SSL pinning
- Cần root BlueStacks hoặc dùng Frida (xem phần dưới)

### Vấn đề 3: Không thấy traffic trong mitmproxy

**Giải pháp**:
- Kiểm tra proxy settings trong BlueStacks
- Thử clear cache của app
- Restart app

## Nếu app dùng SSL Pinning

### Cách 1: Root BlueStacks và cài certificate vào system

```bash
# Root BlueStacks (tùy version)
# Xem: https://www.bstweaker.tk/

# Mount system as read-write
adb root
adb remount

# Copy certificate
adb push mitmproxy-ca-cert.cer /system/etc/security/cacerts/
```

### Cách 2: Dùng Frida để bypass SSL pinning

```bash
# Cài Frida
pip install frida-tools

# Tải Frida server cho Android
# https://github.com/frida/frida/releases

# Push lên BlueStacks
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "/data/local/tmp/frida-server &"

# Chạy script bypass
frida -U -f com.lonoapp.novelfever -l ssl-bypass.js --no-pause
```

## Kết quả mong đợi

Sau khi làm đúng các bước, bạn sẽ thấy:

1. **Trường hợp tốt nhất**: Nội dung đã giải mã trong response
   ```
   Response: "Chương 1\n\nThiếu niên kiếm khách..."
   ```

2. **Trường hợp tìm được key**: APP_KEY trong headers
   ```
   X-App-Key: base64:abcd1234...
   ```

3. **Trường hợp vẫn mã hóa**: Cần dùng Frida để hook

## Lưu ý

- Đảm bảo máy tính và BlueStacks cùng mạng
- Tắt antivirus/firewall nếu cần
- Nếu không được, thử Frida (xem docs/MITMPROXY_GUIDE.md)
