# Hướng dẫn tổng hợp: Tìm APP_KEY và giải mã nội dung

## Tổng quan vấn đề

API trả về nội dung đã mã hóa bằng Laravel Encryption (AES-256-CBC):
```json
{
  "iv": "base64_encoded_iv",
  "value": "base64_encoded_encrypted_content",
  "mac": "hmac_signature",
  "tag": ""
}
```

Để giải mã, cần tìm **APP_KEY** (32 bytes, thường được encode base64).

## Các phương án (theo độ khó tăng dần)

### ⭐ Phương án 1: Dùng mitmproxy (KHUYẾN NGHỊ)

**Độ khó**: ⭐⭐  
**Thời gian**: 30-60 phút  
**Tỷ lệ thành công**: 80%

**Ưu điểm**:
- Dễ thực hiện
- Không cần kiến thức lập trình sâu
- Có thể thấy nội dung đã giải mã trực tiếp

**Bước thực hiện**:
1. Cài mitmproxy: `pip install mitmproxy`
2. Chạy: `mitmweb`
3. Cấu hình proxy trên điện thoại Android
4. Cài certificate từ mitm.it
5. Mở app và đọc truyện
6. Xem traffic để tìm APP_KEY hoặc nội dung đã giải mã

**Chi tiết**: Xem [MITMPROXY_GUIDE.md](MITMPROXY_GUIDE.md)

---

### ⭐⭐ Phương án 2: Dùng reFlutter

**Độ khó**: ⭐⭐  
**Thời gian**: 1-2 giờ  
**Tỷ lệ thành công**: 60%

**Ưu điểm**:
- Tự động decompile Flutter app
- Có thể tìm thấy APP_KEY trong code
- Patch APK để log traffic

**Bước thực hiện**:
1. Clone reFlutter: `git clone https://github.com/Impact-I/reFlutter.git`
2. Chạy: `python reFlutter/reflutter.py MTC.apk`
3. Tìm APP_KEY trong code đã decompile
4. Hoặc cài APK đã patch và xem log

**Chi tiết**: Xem [DART_DECOMPILE_GUIDE.md](DART_DECOMPILE_GUIDE.md)

---

### ⭐⭐⭐ Phương án 3: Dùng Frida Hook

**Độ khó**: ⭐⭐⭐  
**Thời gian**: 2-3 giờ  
**Tỷ lệ thành công**: 70%

**Ưu điểm**:
- Hook runtime để bắt key
- Bypass SSL pinning
- Xem nội dung đã giải mã trong memory

**Bước thực hiện**:
1. Root điện thoại hoặc dùng emulator
2. Cài Frida: `pip install frida-tools`
3. Chạy Frida server trên điện thoại
4. Hook hàm decrypt để log key
5. Mở app và xem log

**Chi tiết**: Xem [MITMPROXY_GUIDE.md](MITMPROXY_GUIDE.md) (phần Frida)

---

### ⭐⭐⭐⭐ Phương án 4: Phân tích với Ghidra

**Độ khó**: ⭐⭐⭐⭐  
**Thời gian**: 4-8 giờ  
**Tỷ lệ thành công**: 40%

**Ưu điểm**:
- Phân tích sâu binary
- Tìm được logic giải mã chính xác
- Không cần chạy app

**Nhược điểm**:
- Cần kiến thức reverse engineering
- Mất nhiều thời gian
- Khó với người mới

**Bước thực hiện**:
1. Tải Ghidra từ https://ghidra-sre.org/
2. Load libapp.so vào Ghidra
3. Tìm hàm decrypt/getChapterContent
4. Phân tích assembly code
5. Tìm APP_KEY trong constants

**Chi tiết**: Xem [DART_DECOMPILE_GUIDE.md](DART_DECOMPILE_GUIDE.md)

---

## Quick Start (Bắt đầu nhanh)

### Bước 1: Thử phương án đơn giản nhất

```bash
# Cài mitmproxy
pip install mitmproxy

# Chạy
mitmweb

# Cấu hình điện thoại và bắt traffic
```

### Bước 2: Nếu không được, thử reFlutter

```bash
# Clone reFlutter
git clone https://github.com/Impact-I/reFlutter.git
cd reFlutter
pip install -r requirements.txt

# Decompile APK
python reflutter.py ../MTC.apk

# Tìm APP_KEY trong code
grep -r "APP_KEY" MTC.apk.reflutter/
grep -r "base64:" MTC.apk.reflutter/
```

### Bước 3: Nếu vẫn không được, thử Frida

```bash
# Cài Frida
pip install frida-tools

# Hook decrypt function
frida -U -f com.lonoapp.novelfever -l frida_hook_decrypt.js --no-pause
```

---

## Scripts hỗ trợ

### 1. Phân tích mitmproxy traffic
```bash
python analyze_mitmproxy_traffic.py traffic.json
```

### 2. Extract Dart snapshot
```bash
python extract_dart_snapshot.py
```

### 3. Phân tích Dart snapshot
```bash
python analyze_dart_snapshot.py
```

### 4. Test giải mã với key
```bash
python test_decrypt_with_key.py "base64:YOUR_KEY_HERE"
```

---

## Khi tìm được APP_KEY

### Test ngay với script
```bash
python test_decrypt_with_key.py "base64:abcd1234..."
```

### Tích hợp vào downloader
Sửa file `mtc/api.py`:
```python
# Thêm APP_KEY
APP_KEY = "base64:YOUR_KEY_HERE"

def decrypt_content(encrypted):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    import base64
    import json
    
    # Parse key
    key = base64.b64decode(APP_KEY[7:])
    
    # Parse encrypted data
    data = json.loads(base64.b64decode(encrypted))
    iv = base64.b64decode(data['iv'])
    value = base64.b64decode(data['value'])
    
    # Decrypt
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(value), AES.block_size)
    
    return decrypted.decode('utf-8')
```

---

## Troubleshooting

### Vấn đề: mitmproxy không bắt được traffic
**Giải pháp**:
- Kiểm tra proxy settings trên điện thoại
- Cài certificate đúng cách
- App có thể dùng SSL pinning → dùng Frida

### Vấn đề: reFlutter không decompile được
**Giải pháp**:
- Thử version khác của reFlutter
- Dùng Ghidra để phân tích thủ công
- Thử extract snapshot thủ công

### Vấn đề: Frida không hook được
**Giải pháp**:
- Kiểm tra Frida server đang chạy
- Kiểm tra package name đúng
- Thử root điện thoại hoặc dùng emulator

### Vấn đề: Giải mã thất bại dù có key
**Giải pháp**:
- Kiểm tra format key (có "base64:" prefix không?)
- Kiểm tra key có đúng 32 bytes không?
- Thử các key khác nhau từ analysis

---

## Kết luận

**Khuyến nghị**: Bắt đầu với **mitmproxy** (dễ nhất, tỷ lệ thành công cao).

Nếu không được, thử theo thứ tự:
1. mitmproxy → 2. reFlutter → 3. Frida → 4. Ghidra

**Lưu ý pháp lý**: Chỉ dùng cho mục đích nghiên cứu và học tập cá nhân.

---

## Tài liệu tham khảo

- [MITMPROXY_GUIDE.md](MITMPROXY_GUIDE.md) - Hướng dẫn chi tiết mitmproxy
- [DART_DECOMPILE_GUIDE.md](DART_DECOMPILE_GUIDE.md) - Hướng dẫn decompile Dart
- [Laravel Encryption](https://laravel.com/docs/encryption) - Tài liệu Laravel
- [reFlutter](https://github.com/Impact-I/reFlutter) - Tool decompile Flutter
- [Frida](https://frida.re/) - Dynamic instrumentation toolkit
