# Hướng dẫn Decompile Dart code từ libapp.so

## Tổng quan
Flutter app được compile thành Dart snapshot trong file `libapp.so`. Ta cần extract và decompile snapshot này để tìm APP_KEY hoặc logic giải mã.

## Bước 1: Chuẩn bị công cụ

### 1.1. Cài đặt Python dependencies
```bash
pip install lief
pip install pyelftools
```

### 1.2. Tải công cụ decompile
```bash
# ReFlutter - công cụ tốt nhất để decompile Flutter
git clone https://github.com/Impact-I/reFlutter.git
cd reFlutter
pip install -r requirements.txt
```

### 1.3. Tải Ghidra (optional, cho phân tích sâu)
- Tải từ: https://ghidra-sre.org/
- Giải nén và chạy `ghidraRun.bat`

## Bước 2: Extract Dart snapshot từ libapp.so

### 2.1. Tìm snapshot offset
```python
#!/usr/bin/env python3
"""Extract Dart snapshot from libapp.so"""
import struct
from pathlib import Path

def find_snapshot_offset(libapp_path):
    """Tìm offset của Dart snapshot trong libapp.so"""
    with open(libapp_path, 'rb') as f:
        data = f.read()
    
    # Tìm magic bytes của Dart snapshot
    # Dart snapshot thường bắt đầu với: 0xf5, 0xf5, 0xdc, 0xdc
    magic = b'\xf5\xf5\xdc\xdc'
    
    offset = data.find(magic)
    if offset != -1:
        print(f"✅ Found Dart snapshot at offset: 0x{offset:x}")
        return offset
    
    # Thử magic khác (Dart 2.x)
    magic2 = b'\xdc\xdc\xf5\xf5'
    offset = data.find(magic2)
    if offset != -1:
        print(f"✅ Found Dart snapshot at offset: 0x{offset:x}")
        return offset
    
    print("❌ Dart snapshot magic not found")
    return None

def extract_snapshot(libapp_path, output_path):
    """Extract snapshot từ libapp.so"""
    offset = find_snapshot_offset(libapp_path)
    if not offset:
        return False
    
    with open(libapp_path, 'rb') as f:
        f.seek(offset)
        snapshot_data = f.read()
    
    with open(output_path, 'wb') as f:
        f.write(snapshot_data)
    
    print(f"✅ Snapshot extracted to: {output_path}")
    print(f"   Size: {len(snapshot_data)} bytes")
    return True

if __name__ == "__main__":
    libapp = Path("extract/lib/arm64-v8a/libapp.so")
    output = Path("dart_snapshot.bin")
    
    if extract_snapshot(libapp, output):
        print("\n✅ Success! Now use reFlutter to decompile.")
    else:
        print("\n❌ Failed to extract snapshot.")
```

### 2.2. Chạy script extract
```bash
python extract_dart_snapshot.py
```

## Bước 3: Decompile với reFlutter

### 3.1. Chạy reFlutter trên APK
```bash
# Decompile toàn bộ APK
python reFlutter/reflutter.py MTC.apk

# Output sẽ ở thư mục: MTC.apk.reflutter
```

### 3.2. Xem kết quả
```bash
cd MTC.apk.reflutter
ls -la

# Tìm file Dart code
find . -name "*.dart" -o -name "*.txt"
```

### 3.3. Tìm APP_KEY trong code
```bash
# Tìm trong các file đã decompile
grep -r "APP_KEY" .
grep -r "encryption" .
grep -r "decrypt" .
grep -r "base64:" .
```

## Bước 4: Phân tích với Ghidra (nếu reFlutter không đủ)

### 4.1. Load libapp.so vào Ghidra
1. Mở Ghidra
2. Create New Project
3. Import File → chọn `libapp.so`
4. Analyze → chọn tất cả options

### 4.2. Tìm hàm giải mã
```
# Tìm trong Symbol Tree:
- decrypt
- AES
- cipher
- getChapterContent
- decryptContent
```

### 4.3. Xem strings
1. Window → Defined Strings
2. Filter: "key", "encrypt", "base64"
3. Double click để xem code sử dụng string đó

## Bước 5: Phân tích Dart snapshot thủ công

### 5.1. Dùng Dart SDK để dump snapshot
```bash
# Cài Dart SDK
# Windows: choco install dart-sdk
# Linux: sudo apt install dart

# Dump snapshot info
dart --snapshot-kind=app-jit --snapshot=dart_snapshot.bin analyze
```

### 5.2. Script Python để parse snapshot
```python
#!/usr/bin/env python3
"""Parse Dart snapshot để tìm strings và constants."""
import struct
from pathlib import Path

def parse_dart_snapshot(snapshot_path):
    """Parse Dart snapshot và extract strings."""
    with open(snapshot_path, 'rb') as f:
        data = f.read()
    
    print(f"Snapshot size: {len(data)} bytes")
    
    # Tìm các string có thể là APP_KEY (base64, 40-50 chars)
    strings = []
    current = b''
    
    for byte in data:
        if 32 <= byte <= 126:  # Printable ASCII
            current += bytes([byte])
        else:
            if len(current) >= 40:  # Potential key
                s = current.decode('ascii', errors='ignore')
                if is_potential_key(s):
                    strings.append(s)
            current = b''
    
    return strings

def is_potential_key(s):
    """Kiểm tra xem string có phải là key không."""
    # Base64 key thường có format: [A-Za-z0-9+/]{40,}={0,2}
    import re
    if re.match(r'^[A-Za-z0-9+/]{40,}={0,2}$', s):
        return True
    
    # Laravel key format: base64:...
    if s.startswith('base64:'):
        return True
    
    return False

if __name__ == "__main__":
    snapshot = Path("dart_snapshot.bin")
    if snapshot.exists():
        keys = parse_dart_snapshot(snapshot)
        
        print(f"\n{'='*60}")
        print(f"Found {len(keys)} potential keys:")
        print('='*60)
        
        for key in keys:
            print(f"\n{key}")
    else:
        print("❌ dart_snapshot.bin not found. Run extract_dart_snapshot.py first.")
```

## Bước 6: Tìm logic giải mã trong code

### 6.1. Tìm file chứa logic giải mã
Trong Flutter app, logic giải mã thường ở:
```
lib/models/chapter.dart
lib/services/api_service.dart
lib/utils/encryption.dart
lib/helpers/decrypt_helper.dart
```

### 6.2. Pattern để tìm
```dart
// Tìm các pattern này trong code đã decompile:

// 1. Import crypto
import 'package:crypto/crypto.dart';
import 'package:encrypt/encrypt.dart';

// 2. Hàm decrypt
String decrypt(String encrypted) {
  final key = Key.fromBase64('...');  // <-- APP_KEY ở đây!
  final iv = IV.fromBase64('...');
  final encrypter = Encrypter(AES(key));
  return encrypter.decrypt64(encrypted, iv: iv);
}

// 3. Constant key
const String APP_KEY = 'base64:...';
const String ENCRYPTION_KEY = '...';
```

## Bước 7: Alternative - Patch APK để log key

### 7.1. Dùng reFlutter để patch
```bash
# reFlutter tự động patch APK để log tất cả traffic
python reFlutter/reflutter.py MTC.apk

# Cài APK đã patch
adb install MTC.apk.reflutter/release.RE.apk

# Xem log
adb logcat | grep -i "key\|encrypt\|decrypt"
```

### 7.2. Dùng Frida để hook hàm decrypt
```javascript
// frida_hook_decrypt.js
Java.perform(function() {
    console.log("Hooking decrypt functions...");
    
    // Hook Flutter decrypt
    var System = Java.use('java.lang.System');
    System.loadLibrary.implementation = function(library) {
        console.log("Loading library: " + library);
        var result = this.loadLibrary(library);
        
        if (library === "flutter") {
            console.log("Flutter library loaded!");
            // Hook native functions here
        }
        
        return result;
    };
    
    // Hook AES decrypt
    try {
        var Cipher = Java.use('javax.crypto.Cipher');
        Cipher.doFinal.overload('[B').implementation = function(input) {
            console.log("Cipher.doFinal called");
            console.log("Input: " + bytesToHex(input));
            
            var result = this.doFinal(input);
            console.log("Output: " + bytesToString(result));
            
            return result;
        };
    } catch(e) {
        console.log("Failed to hook Cipher: " + e);
    }
});

function bytesToHex(bytes) {
    var hex = '';
    for (var i = 0; i < Math.min(bytes.length, 50); i++) {
        hex += ('0' + (bytes[i] & 0xFF).toString(16)).slice(-2);
    }
    return hex;
}

function bytesToString(bytes) {
    var str = '';
    for (var i = 0; i < Math.min(bytes.length, 100); i++) {
        str += String.fromCharCode(bytes[i]);
    }
    return str;
}
```

### 7.3. Chạy Frida hook
```bash
# Chạy app với Frida
frida -U -f com.lonoapp.novelfever -l frida_hook_decrypt.js --no-pause

# Mở app và đọc truyện, xem log
```

## Bước 8: Kết quả mong đợi

### Trường hợp 1: Tìm thấy APP_KEY trong code
```dart
const String APP_KEY = 'base64:abcd1234567890...';
```
→ ✅ Dùng key này để giải mã!

### Trường hợp 2: Tìm thấy logic giải mã
```dart
String decrypt(String encrypted) {
  // Logic giải mã ở đây
  // Ta có thể port sang Python
}
```
→ ✅ Port logic sang Python!

### Trường hợp 3: Key được lấy từ server
```dart
final key = await api.getEncryptionKey();
```
→ ⚠️ Cần dùng mitmproxy để bắt request này

## Tools Summary

| Tool | Mục đích | Độ khó |
|------|----------|--------|
| reFlutter | Decompile Flutter APK | ⭐⭐ |
| Ghidra | Phân tích binary | ⭐⭐⭐⭐ |
| Frida | Hook runtime | ⭐⭐⭐ |
| mitmproxy | Bắt network traffic | ⭐⭐ |

## Khuyến nghị

1. **Bắt đầu với**: reFlutter (dễ nhất)
2. **Nếu không được**: Dùng Frida để hook
3. **Cuối cùng**: Phân tích với Ghidra (khó nhất)

## Lưu ý pháp lý

⚠️ **QUAN TRỌNG**: 
- Chỉ dùng cho mục đích nghiên cứu và học tập cá nhân
- Không phân phối hoặc sử dụng thương mại
- Tôn trọng bản quyền của tác giả và nhà phát hành
