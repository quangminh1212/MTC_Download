# MTC Novel Downloader v2.0

Công cụ tải truyện chữ từ nền tảng **MTC / NovelFever (Lono App)** thông qua API — không cần giả lập Android, ADB, BlueStacks hay Frida. Hỗ trợ cả giao diện đồ họa (GUI) lẫn dòng lệnh (CLI), tự động giải mã AES nội dung chương VIP.

---

## Mục lục

- [Tính năng](#tính-năng)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Xác thực — Token](#xác-thực--token)
- [Sử dụng CLI](#sử-dụng-cli)
- [Sử dụng GUI](#sử-dụng-gui)
- [Hot-reload (Phát triển)](#hot-reload-phát-triển)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Chi tiết kỹ thuật](#chi-tiết-kỹ-thuật)
- [Scripts tiện ích](#scripts-tiện-ích)
- [Phát triển & Kiểm thử](#phát-triển--kiểm-thử)
- [Xử lý sự cố](#xử-lý-sự-cố)
- [License](#license)

---

## Tính năng

| Tính năng | Mô tả |
|---|---|
| **Tải theo tên** | Tìm và tải truyện chỉ bằng tên (tìm kiếm gần đúng trên API) |
| **Tải hàng loạt** | `--all` để tải toàn bộ catalog, `--completed` chỉ tải truyện đã hoàn thành |
| **Khoảng chương** | `--start` / `--end` giới hạn phạm vi chương cần tải |
| **Giải mã AES** | Tự động giải mã nội dung chương mã hóa AES/CBC/PKCS5 |
| **Bỏ qua chương đã tải** | Mặc định skip chương có sẵn trên đĩa, `--no-skip` để tải lại |
| **GUI tkinter** | Giao diện đồ họa với tìm kiếm, quản lý thư viện, log trực tiếp |
| **Hot-reload** | Tự khởi động lại khi phát hiện thay đổi file `.py` (chế độ dev) |
| **Sửa encoding** | Script sửa lỗi encoding UTF-8 (mojibake) bằng `ftfy` |
| **Tải batch** | Script tải hàng loạt tự động |
| **Catalog offline** | Lưu cache danh sách truyện vào `data/all_books.json` |

---

## Yêu cầu hệ thống

- **Python** ≥ 3.10
- **Hệ điều hành**: Windows (đã test), Linux/macOS (cần test thêm)
- Kết nối Internet

---

## Cài đặt

### Cách 1 — Editable install (khuyến nghị cho dev)

```powershell
git clone <repo-url> && cd MTC_Download
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate       # Linux/macOS
pip install -e ".[dev]"
```

Sau khi cài, lệnh `mtc-download` sẽ có sẵn trong PATH của virtualenv.

### Cách 2 — Chỉ cài dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Xác thực — Token

Ứng dụng cần **Bearer token** để truy cập API (đặc biệt là chương VIP/khóa).

1. Cài app **Lono** (MTC/NovelFever) trên điện thoại hoặc giả lập.
2. Đăng nhập tài khoản có VIP.
3. Bắt request HTTP (dùng mitmproxy, Charles Proxy, v.v.) lấy header `Authorization: Bearer <token>`.
4. Tạo file `token.txt` ở **thư mục gốc** dự án, dán token vào (chỉ token, không có prefix `Bearer`).

```
eyJhbGciOiJIUzI1NiIs...
```

> **Lưu ý**: `token.txt` đã được thêm vào `.gitignore`. Không commit token lên repository.

---

## Sử dụng CLI

Sau khi cài editable (`pip install -e .`), dùng lệnh `mtc-download`. Nếu chỉ cài requirements, chạy trực tiếp `python -m mtc.cli`.

```powershell
# ── Tải một truyện theo tên ──────────────────────────────────────
mtc-download "Vạn Biến Hồn Đế"

# ── Tải theo ID truyện ───────────────────────────────────────────
mtc-download --id 12345

# ── Giới hạn khoảng chương ───────────────────────────────────────
mtc-download "Vạn Biến Hồn Đế" --start 1 --end 100

# ── Tải tất cả truyện trong catalog ──────────────────────────────
mtc-download --all

# ── Chỉ tải truyện đã hoàn thành ─────────────────────────────────
mtc-download --all --completed

# ── Làm mới catalog từ API rồi tải tất cả ────────────────────────
mtc-download --refresh --all

# ── Liệt kê danh sách truyện trong catalog ───────────────────────
mtc-download --list

# ── Giới hạn số lượng khi liệt kê ────────────────────────────────
mtc-download --list --limit 20

# ── Tìm kiếm truyện trên API ─────────────────────────────────────
mtc-download --search "Hồn Đế"

# ── Tải lại chương đã có (không skip) ─────────────────────────────
mtc-download "Vạn Biến Hồn Đế" --no-skip

# ── Chọn thư mục xuất ────────────────────────────────────────────
mtc-download "Vạn Biến Hồn Đế" -o D:\Truyen
```

### Tất cả tùy chọn CLI

| Tùy chọn | Mô tả |
|---|---|
| `book` (positional) | Tên truyện cần tải |
| `--id ID` | Tải theo ID truyện |
| `--all` | Tải tất cả truyện trong catalog |
| `--refresh` | Làm mới catalog từ API trước khi tải |
| `--completed` | Chỉ tải truyện có trạng thái hoàn thành |
| `--list` | Liệt kê danh sách truyện trong catalog |
| `--search QUERY` | Tìm kiếm truyện trên API |
| `--start N` | Bắt đầu từ chương thứ N |
| `--end N` | Kết thúc tại chương thứ N |
| `--limit N` | Giới hạn số lượng kết quả |
| `--no-skip` | Tải lại chương đã có trên đĩa |
| `-o`, `--output DIR` | Thư mục xuất file (mặc định: `novel_exports/`) |

---

## Sử dụng GUI

### Chạy trực tiếp

```powershell
python mtc/app.py
```

### Chạy với hot-reload (khuyến nghị khi dev)

```powershell
scripts\run.bat
```

**Giao diện GUI** (800×600, bảng màu Google-style):

- **Thanh tìm kiếm**: Nhập tên truyện → tìm kiếm realtime trên API
- **Danh sách thư viện**: Duyệt catalog truyện đã lưu
- **Panel tải**: Chọn truyện → tải về với tiến trình hiển thị
- **Log viewer**: Vùng log tối (#1e1e1e) hiển thị hoạt động realtime
- **Nút Refresh**: Cập nhật catalog từ API

---

## Hot-reload (Phát triển)

Khi chạy qua `scripts/run.bat`, ứng dụng hoạt động với cơ chế hot-reload:

1. Biến môi trường `MTC_HOT_RELOAD=1` được set.
2. `app.py` khởi chạy background thread `_file_watcher` theo dõi tất cả file `.py` trong thư mục `mtc/`.
3. Mỗi **2 giây**, watcher so sánh modification time của các file.
4. Nếu phát hiện thay đổi → app thoát với **exit code 42**.
5. `run.bat` nhận exit code 42 → tự động chạy lại app (loop vô hạn).
6. Exit code khác 42 → dừng hoàn toàn.

---

## Cấu trúc dự án

```
MTC_Download/
├── .gitignore                  # Git ignore rules
├── README.md                   # File này
├── pyproject.toml              # Build config, metadata, dependencies
├── requirements.txt            # Pinned dependencies
│
├── mtc/                        # 📦 Package chính
│   ├── __init__.py             # Package init, version info
│   ├── api.py                  # API client — HTTP session, giải mã AES
│   ├── app.py                  # Entry GUI — tkinter launcher, hot-reload
│   ├── cli.py                  # Entry CLI — argparse, subcommands
│   ├── config.py               # Constants, paths, palette, logging setup
│   ├── downloader.py           # Download orchestrator — tải & lưu chương
│   ├── ui.py                   # Tkinter GUI — App class 800×600
│   └── utils.py                # Tiện ích — sanitize filename, format size
│
├── scripts/                    # 🔧 Scripts tiện ích
│   ├── run.bat                 # Launcher Windows với hot-reload loop
│   ├── fix_encoding.py         # Sửa lỗi encoding UTF-8 (ftfy)
│   └── batch.py                # Tải truyện hàng loạt tự động
│
├── legacy/                     # 📁 Files cũ (deprecated)
│   ├── old_adb.py              # Phương pháp cũ qua ADB + BlueStacks
│   ├── old_config.py           # Config cũ
│   ├── old_utils.py            # Utils cũ
│   └── MTC.apk                 # APK gốc (nếu có)
│
├── data/                       # 📊 Dữ liệu runtime
│   ├── all_books.json          # Cache catalog truyện
│   └── ...                     # UI dump, danh sách truyện
│
├── novel_exports/              # 📖 Thư mục xuất truyện (mặc định)
│   └── *.txt                   # File truyện đã tải (UTF-8)
│
└── tests/                      # 🧪 Unit tests
    ├── conftest.py             # Pytest fixtures
    └── test_api.py             # Tests cho API module
```

---

## Chi tiết kỹ thuật

### API

- **Base URL**: `https://android.lonoapp.net/api`
- **User-Agent**: `Dart/3.0 (dart:io)`
- **Xác thực**: Header `Authorization: Bearer <token>` (đọc từ `token.txt`)
- **Endpoints chính**:
  - Tìm kiếm: `GET /search?keyword=...`
  - Danh sách chương: `GET /book/{id}/chapters`
  - Nội dung chương: `GET /chapter/{id}/content`

### Giải mã nội dung (AES)

Nội dung chương VIP được mã hóa AES/CBC/PKCS5Padding:

1. Nhận response content dạng bytes.
2. Trích xuất **key** từ bytes `[17:33]` (16 bytes).
3. Phần còn lại decode Base64 → JSON chứa `iv` và `value`.
4. Giải mã AES-CBC với key và iv → plaintext UTF-8.
5. Unpad PKCS5 → nội dung chương sạch.

### Logging

- **Dual Logger** (`_DualLogger`): Ghi đồng thời ra console và file.
- **Console**: Fix UTF-8 cho Windows console (BOM + reconfigure).
- **File**: `RotatingFileHandler` — tối đa **5 MB/file**, giữ **3 bản backup**.
- **File log**: `log.txt` tại thư mục gốc dự án.

### Output

- Truyện được lưu thành file `.txt` (UTF-8) trong thư mục `novel_exports/` (hoặc thư mục tùy chỉnh qua `-o`).
- Tên file = tên truyện đã sanitize (loại bỏ ký tự đặc biệt).
- Mỗi chương ghi tiêu đề + nội dung, phân cách bằng dòng trống.

---

## Scripts tiện ích

### `scripts/fix_encoding.py`

Sửa lỗi encoding (mojibake) trong các file `.txt` đã tải:

```powershell
python scripts/fix_encoding.py
```

- Quét thư mục `exports/` và `novel_exports/`.
- Dùng thư viện `ftfy` để tự động phát hiện và sửa lỗi encoding.
- Ghi kết quả vào thư mục riêng (không ghi đè file gốc).

### `scripts/batch.py`

Tải hàng loạt truyện tự động:

```powershell
python scripts/batch.py
```

### `scripts/run.bat`

Launcher Windows với hot-reload loop cho phát triển:

```powershell
scripts\run.bat
```

---

## Phát triển & Kiểm thử

### Cài đặt môi trường dev

```powershell
pip install -e ".[dev]"
```

Dependencies dev bao gồm: `pytest>=8.0`, `pytest-timeout>=2.3`.

### Chạy tests

```powershell
pytest
# hoặc với verbose
pytest -v
# chạy test cụ thể
pytest tests/test_api.py -v
```

### Cấu hình pytest (trong `pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

---

## Xử lý sự cố

| Vấn đề | Giải pháp |
|---|---|
| `Token hết hạn / 401 Unauthorized` | Lấy token mới từ app Lono và cập nhật `token.txt` |
| `Không tìm thấy truyện` | Kiểm tra tên truyện chính xác, thử `--search` để tìm |
| `Lỗi encoding / ký tự lạ` | Chạy `python scripts/fix_encoding.py` |
| `GUI không mở` | Đảm bảo có tkinter: `python -c "import tkinter"` |
| `ModuleNotFoundError: mtc` | Cài editable: `pip install -e .` |
| `Hot-reload không hoạt động` | Chạy qua `scripts\run.bat`, không chạy trực tiếp `app.py` |
| `Chương tải thiếu / lỗi` | Dùng `--no-skip` để tải lại, kiểm tra kết nối mạng |
| `Console hiển thị lỗi Unicode` | Python ≥3.10 trên Windows, hoặc dùng Windows Terminal |

---

## Dependencies

| Package | Phiên bản | Mục đích |
|---|---|---|
| `requests` | ≥ 2.31 | HTTP client cho API calls |
| `urllib3` | ≥ 2.0 | HTTP backend |
| `pycryptodome` | ≥ 3.19 | Giải mã AES/CBC nội dung chương |
| `ftfy` | ≥ 7.1.1 | Sửa lỗi encoding UTF-8 |

---

## License

Private project — không phân phối công khai.
