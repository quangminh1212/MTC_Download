# Hướng dẫn dùng mitmproxy để bắt APP_KEY

## Tổng quan
mitmproxy là công cụ để bắt và phân tích HTTP/HTTPS traffic. Ta sẽ dùng nó để xem app gửi/nhận gì từ server, từ đó tìm APP_KEY hoặc nội dung đã giải mã.

## Bước 1: Cài đặt mitmproxy

### Windows
```bash
# Cài qua pip
pip install mitmproxy

# Hoặc tải binary từ: https://mitmproxy.org/
```

### Kiểm tra cài đặt
```bash
mitmproxy --version
```

## Bước 2: Chuẩn bị thiết bị Android

### 2.1. Cài đặt certificate
1. Chạy mitmproxy:
   ```bash
   mitmweb
   ```
2. Truy cập `http://mitm.it` trên điện thoại Android
3. Tải và cài certificate cho Android

### 2.2. Cấu hình proxy trên Android
1. Vào **Settings** → **Wi-Fi**
2. Long press vào mạng Wi-Fi đang kết nối
3. Chọn **Modify network** → **Advanced options**
4. **Proxy**: Manual
5. **Proxy hostname**: IP máy tính (ví dụ: 192.168.1.100)
6. **Proxy port**: 8080
7. Save

### 2.3. Tìm IP máy tính
```bash
# Windows
ipconfig

# Tìm IPv4 Address của mạng Wi-Fi
```

## Bước 3: Chạy mitmproxy và bắt traffic

### 3.1. Chạy mitmproxy với filter
```bash
# Chỉ bắt traffic từ API
mitmweb --set flow_detail=3 --set console_eventlog_verbosity=debug

# Hoặc dùng mitmdump để lưu vào file
mitmdump -w traffic.flow "~d api.lonoapp.net"
```

### 3.2. Mở app và tải truyện
1. Mở app NovelFever trên điện thoại
2. Tìm và mở một truyện bất kỳ
3. Đọc vài chương
4. Quan sát traffic trên mitmproxy

## Bước 4: Phân tích traffic

### 4.1. Tìm request đến `/chapters/{id}`
- Xem request headers (có thể có Authorization token)
- Xem response body (nội dung đã giải mã hoặc còn mã hóa)

### 4.2. Tìm APP_KEY
APP_KEY có thể xuất hiện ở:
- **Request headers**: `X-App-Key`, `Authorization`
- **Response headers**: `X-Encryption-Key`
- **JavaScript/Config files**: Các request đến `/config`, `/app.js`
- **Nội dung đã giải mã**: Nếu app giải mã trước khi hiển thị, ta sẽ thấy plain text

### 4.3. Script Python để phân tích traffic
```python
#!/usr/bin/env python3
"""Phân tích mitmproxy flow file để tìm APP_KEY."""
from mitmproxy import io
from mitmproxy.exceptions import FlowReadException
import sys

def analyze_flow(flow_file):
    """Phân tích flow file."""
    with open(flow_file, "rb") as f:
        reader = io.FlowReader(f)
        
        for flow in reader.stream():
            if hasattr(flow, 'request'):
                req = flow.request
                resp = flow.response
                
                # Chỉ xem API requests
                if 'api.lonoapp.net' in req.pretty_host:
                    print(f"\n{'='*60}")
                    print(f"URL: {req.pretty_url}")
                    print(f"Method: {req.method}")
                    
                    # Xem headers
                    print(f"\nRequest Headers:")
                    for k, v in req.headers.items():
                        if 'key' in k.lower() or 'auth' in k.lower():
                            print(f"  {k}: {v}")
                    
                    # Xem response
                    if resp:
                        print(f"\nResponse Status: {resp.status_code}")
                        
                        # Xem response headers
                        print(f"Response Headers:")
                        for k, v in resp.headers.items():
                            if 'key' in k.lower() or 'encrypt' in k.lower():
                                print(f"  {k}: {v}")
                        
                        # Xem content
                        content = resp.text[:500] if resp.text else ""
                        if content and not content.startswith("eyJ"):
                            print(f"\n✅ Plain text content found!")
                            print(f"First 200 chars: {content[:200]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_traffic.py traffic.flow")
        sys.exit(1)
    
    analyze_flow(sys.argv[1])
```

## Bước 5: Bypass SSL Pinning (nếu cần)

Nếu app dùng SSL pinning, mitmproxy sẽ không bắt được traffic. Cần:

### 5.1. Root điện thoại hoặc dùng emulator
- Dùng Android emulator (Android Studio)
- Hoặc root điện thoại thật

### 5.2. Cài Frida để bypass SSL pinning
```bash
# Cài Frida
pip install frida-tools

# Tải Frida server cho Android
# https://github.com/frida/frida/releases

# Push lên điện thoại
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "/data/local/tmp/frida-server &"

# Chạy script bypass SSL pinning
frida -U -f com.lonoapp.novelfever -l ssl-bypass.js --no-pause
```

### 5.3. Script Frida bypass SSL pinning
Tạo file `ssl-bypass.js`:
```javascript
Java.perform(function() {
    console.log("Bypassing SSL Pinning...");
    
    // Bypass OkHttp
    var CertificatePinner = Java.use("okhttp3.CertificatePinner");
    CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function() {
        console.log("SSL Pinning bypassed for: " + arguments[0]);
    };
    
    // Bypass TrustManager
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    
    var TrustManager = Java.registerClass({
        name: 'com.sensepost.test.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });
    
    var TrustManagers = [TrustManager.$new()];
    var SSLContext_init = SSLContext.init.overload(
        '[Ljavax.net.ssl.KeyManager;', 
        '[Ljavax.net.ssl.TrustManager;', 
        'java.security.SecureRandom'
    );
    
    SSLContext_init.implementation = function(keyManager, trustManager, secureRandom) {
        console.log("SSLContext.init() called");
        SSLContext_init.call(this, keyManager, TrustManagers, secureRandom);
    };
    
    console.log("SSL Pinning bypass complete!");
});
```

## Bước 6: Kết quả mong đợi

Sau khi bắt được traffic, bạn sẽ thấy:

### Trường hợp 1: Nội dung đã giải mã
```
Response body: "Chương 1\n\nThiếu niên kiếm khách..."
```
→ App giải mã trước khi hiển thị, ta có thể đọc trực tiếp!

### Trường hợp 2: Tìm thấy APP_KEY
```
Request header: X-App-Key: base64:abcd1234...
```
→ Dùng key này để giải mã!

### Trường hợp 3: Vẫn mã hóa
```
Response body: "eyJpdiI6I..."
```
→ Cần thử phương án khác (decompile Dart)

## Lưu ý

1. **Hợp pháp**: Chỉ dùng cho mục đích nghiên cứu cá nhân
2. **Mạng**: Máy tính và điện thoại phải cùng mạng Wi-Fi
3. **Certificate**: Phải cài certificate mitmproxy trên điện thoại
4. **SSL Pinning**: Nếu app dùng SSL pinning, cần root + Frida

## Troubleshooting

### Không bắt được traffic
- Kiểm tra proxy settings trên điện thoại
- Kiểm tra firewall trên máy tính
- Thử tắt/bật Wi-Fi trên điện thoại

### Certificate error
- Cài lại certificate từ mitm.it
- Trên Android 7+, cần cài certificate vào System store (cần root)

### App không kết nối được
- App có thể dùng SSL pinning
- Cần dùng Frida để bypass (xem Bước 5)
