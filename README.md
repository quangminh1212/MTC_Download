# MTC Novel Downloader

Công cụ tải truyện từ MTC (mtruyen.com) qua API với hỗ trợ tự động giải mã.

## Tính năng

- ✅ Tải truyện qua API
- ✅ Tự động giải mã nội dung (khi có key)
- ✅ Lưu truyện vào thư mục `extract/novels/`
- ✅ Hỗ trợ tìm encryption key từ nhiều nguồn
- ✅ Batch download nhiều truyện

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng nhanh

### 1. Tải một truyện với auto-decrypt

```bash
python download_and_decrypt.py "Tên Truyện"
```

### 2. Tải vào thư mục extract

```bash
# Tải 1 truyện theo tên
python download_to_extract.py "Tên Truyện"

# Tải 1 truyện theo ID
python download_to_extract.py --id 12345
```

### 3. Tải nhiều truyện

```bash
# Tải tất cả từ catalog
python download_batch_to_extract.py

# Cập nhật catalog rồi tải
python download_batch_to_extract.py --refresh

# Chỉ tải truyện hoàn thành
python download_batch_to_extract.py --completed

# Giới hạn số lượng
python download_batch_to_extract.py --limit 10
```

### 3. Sử dụng CLI chính (tải vào folder downloads)

```bash
# Tải 1 truyện
python download/cli.py "Tên Truyện"

# Tìm kiếm
python download/cli.py --search "keyword"

# Liệt kê catalog
python download/cli.py --list

# Tải tất cả
python download/cli.py --all

# Tải truyện hoàn thành
python download/cli.py --all --completed
```

## Cấu trúc thư mục

```
.
├── download/           # CLI module
├── mtc/               # Core modules
│   ├── api.py        # API client
│   ├── config.py     # Configuration
│   ├── downloader.py # Download logic
│   └── utils.py      # Utilities
├── extract/          # Nơi lưu truyện
│   └── novels/       # Truyện được tải về
├── downloads/        # Folder mặc định của CLI
└── data/             # Cache và catalog
```

## Token (Optional)

Nếu cần token để truy cập API, tạo file `token.txt` ở thư mục gốc:

```
your_api_token_here
```

## Vấn đề hiện tại

**Nội dung truyện bị mã hóa Laravel (AES-256-CBC)**

Cần tìm encryption key để giải mã. Xem hướng dẫn chi tiết tại [HUONG_DAN_TIM_KEY.md](HUONG_DAN_TIM_KEY.md)

## Công cụ tìm key

| Tool | Mô tả |
|------|-------|
| `find_key_advanced.py` | Tìm key trong libapp.so (đã tìm 178 hex keys) |
| `extract_strings_from_apk.py` | Extract strings từ DEX files (1545 strings) |
| `test_all_keys.py` | Test tất cả keys đã tìm được |
| `brute_force_common_keys.py` | Thử các pattern key phổ biến |
| `test_decrypt_with_key.py` | Test một key cụ thể |

## Phương pháp tìm key (Khuyến nghị)

### Phương pháp 1: mitmproxy (Dễ nhất) ⭐

```bash
# Cài đặt
pip install mitmproxy

# Chạy
mitmweb --listen-port 8080

# Cấu hình BlueStacks:
# Settings → Network → Manual Proxy
# Host: 127.0.0.1, Port: 8080
# Cài cert từ http://mitm.it

# Chạy app MTC và đọc truyện
# Xem traffic tại http://127.0.0.1:8081
# Tìm encryption key trong headers hoặc response
```

### Phương pháp 2: Frida (Nâng cao)

```bash
pip install frida-tools
frida -U -f com.lonoapp.mtc -l hook_decrypt.js
```

### Phương pháp 3: Memory dump

Dùng GameGuardian search "base64:" trong memory khi app đang chạy.

### Phương pháp 4: Decompile Flutter

```bash
git clone https://github.com/Impact-I/reFlutter
python reFlutter.py MTC.apk
```

## Khi đã có key

### 1. Lưu key

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

## Kết quả đã thử

- ❌ 178 hex keys từ libapp.so - không hoạt động
- ❌ 1545 strings từ DEX files - không tìm thấy key
- ❌ Common key patterns - không hoạt động
- ⏳ Cần dùng mitmproxy/Frida để bắt key trong runtime

## Tài liệu

- [HUONG_DAN_TIM_KEY.md](HUONG_DAN_TIM_KEY.md) - Hướng dẫn chi tiết 4 phương pháp tìm key
- [TONG_KET.md](TONG_KET.md) - Tổng kết dự án và bước tiếp theo

## License

MIT
