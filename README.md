# MTC Novel Downloader v2.0

Tải truyện từ MTC/NovelFever qua API — không cần ADB, BlueStacks, hay Frida.

## Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Sử dụng

### Token xác thực

Đặt file `token.txt` ở thư mục gốc chứa Bearer token (lấy từ app).
Token cần thiết để tải chương VIP/khóa.

### CLI (`download.py`)

```powershell
# Tải một truyện
python download.py "Vạn Biến Hồn Đế"

# Tải một truyện với khoảng chương
python download.py "Vạn Biến Hồn Đế" --start 1 --end 100

# Cập nhật catalog và tải tất cả
python download.py --refresh --all

# Chỉ tải truyện hoàn thành
python download.py --all --completed

# Liệt kê catalog
python download.py --list

# Tìm kiếm trên API
python download.py --search "Hồn Đế"
```

### GUI

```powershell
python gui.py
# hoặc với hot-reload:
run.bat
```

## Cấu trúc dự án

```
download.py          # CLI chính
gui.py               # GUI (tkinter)
run.bat              # Launcher với hot-reload
mtc/
  __init__.py        # Package, version
  config.py          # Cấu hình, paths, logging
  api.py             # API client (HTTP, mã hóa AES)
  downloader.py      # Orchestrator tải truyện
  ui.py              # Tkinter GUI
  utils.py           # Tiện ích file system
data/
  all_books.json     # Catalog truyện
downloads/           # Thư mục output
token.txt            # Bearer token (không commit)
```

## Dependencies

- `requests` — HTTP client
- `pycryptodome` — AES giải mã nội dung chương
- `ftfy` — Sửa encoding text
- `urllib3` — HTTP backend
