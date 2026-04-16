# MTC Novel Downloader - Tổng kết

## Đã hoàn thành

### 1. Hệ thống tải truyện qua API ✅
- `mtc/api.py` - API client để gọi MTC API
- `mtc/downloader.py` - Logic tải truyện và chương
- `download_to_extract.py` - Script tải đơn lẻ
- `download_and_decrypt.py` - Script tải với tự động giải mã

### 2. Công cụ tìm encryption key 🔍
- `find_key_advanced.py` - Tìm key trong libapp.so (178 hex keys)
- `extract_strings_from_apk.py` - Extract strings từ DEX files
- `test_all_keys.py` - Test tất cả keys tìm được
- `brute_force_common_keys.py` - Thử các pattern key phổ biến
- `test_decrypt_with_key.py` - Test một key cụ thể

### 3. Tài liệu hướng dẫn 📚
- `HUONG_DAN_TIM_KEY.md` - Hướng dẫn chi tiết 4 phương pháp tìm key

## Vấn đề hiện tại ⚠️

**Nội dung truyện bị mã hóa Laravel (AES-256-CBC)**

- Đã thử 178 hex keys từ libapp.so → Không hoạt động
- Đã thử các pattern key phổ biến → Không hoạt động  
- Đã extract 1545 strings từ DEX files → Không tìm thấy key
- API có vấn đề SSL khi test trực tiếp

## Giải pháp đề xuất 💡

### Phương pháp 1: mitmproxy (Dễ nhất)
```bash
# Cài đặt
pip install mitmproxy

# Chạy
mitmweb --listen-port 8080

# Cấu hình BlueStacks proxy: 127.0.0.1:8080
# Cài cert từ http://mitm.it
# Chạy app và đọc truyện
# Xem traffic tại http://127.0.0.1:8081
# Tìm header X-Encryption-Key hoặc tương tự
```

### Phương pháp 2: Frida (Nâng cao)
```bash
pip install frida-tools
frida -U -f com.lonoapp.mtc -l hook_decrypt.js
```

### Phương pháp 3: Memory dump
- Dùng GameGuardian search "base64:" trong memory khi app đang chạy

### Phương pháp 4: Decompile Flutter
```bash
git clone https://github.com/Impact-I/reFlutter
python reFlutter.py MTC.apk
```

## Cách sử dụng khi có key 🔑

### 1. Lưu key vào file
```bash
echo "base64:YOUR_KEY_HERE" > WORKING_KEY.txt
```

### 2. Test key
```bash
python test_decrypt_with_key.py "base64:YOUR_KEY_HERE"
```

### 3. Tải truyện với auto-decrypt
```bash
python download_and_decrypt.py "Tên Truyện"
```

## Cấu trúc thư mục 📁

```
MTC_Download/
├── extract/
│   ├── novels/          # Truyện đã tải (encrypted)
│   ├── lib/             # Native libraries
│   ├── assets/          # App assets
│   └── classes*.dex     # DEX files
├── mtc/
│   ├── api.py           # API client
│   ├── downloader.py    # Download logic
│   ├── config.py        # Configuration
│   └── utils.py         # Utilities
├── data/
│   └── all_books.json   # Catalog cache
├── download_and_decrypt.py    # Main downloader
├── test_decrypt_with_key.py   # Key tester
└── HUONG_DAN_TIM_KEY.md       # Detailed guide
```

## Scripts chính 🛠️

| Script | Mục đích |
|--------|----------|
| `download_and_decrypt.py` | Tải truyện với auto-decrypt |
| `test_decrypt_with_key.py` | Test một key |
| `find_key_advanced.py` | Tìm key trong libapp.so |
| `extract_strings_from_apk.py` | Extract strings từ APK |
| `brute_force_common_keys.py` | Thử pattern keys |

## Bước tiếp theo 🎯

1. **Ưu tiên cao**: Chạy app với mitmproxy để bắt key
2. **Thay thế**: Dùng Frida hook AES decryption
3. **Cuối cùng**: Decompile Flutter app để tìm logic generate key

## Ghi chú quan trọng ⚠️

- Key có thể khác nhau cho mỗi user/device
- Key có thể được generate động từ device ID hoặc token
- Nếu key thay đổi thường xuyên, cần hook function để lấy key mỗi lần
- Không commit key vào git (đã thêm vào .gitignore)

## Liên hệ & Hỗ trợ 📧

Nếu cần hỗ trợ thêm, xem:
- `HUONG_DAN_TIM_KEY.md` - Hướng dẫn chi tiết
- `README.md` - Tài liệu chính
