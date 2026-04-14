# MTC Novel Downloader

Công cụ tải truyện từ MTC/NovelFever API.

## Cài đặt

```bash
pip install -e .
```

## Sử dụng

### 1. Tải truyện vào folder extract

```bash
# Tải 1 truyện theo tên
python download_to_extract.py "Tên Truyện"

# Tải 1 truyện theo ID
python download_to_extract.py --id 12345
```

### 2. Tải nhiều truyện vào folder extract

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
