# Hướng dẫn sử dụng Snyk Commands trong Kiro

## 1. Snyk Trust Command

### Mục đích
Trust một folder để cho phép Snyk scan mã nguồn trong đó.

### Cú pháp
```bash
snyk trust <path>
```

### Ví dụ sử dụng trong project này

```bash
# Trust thư mục gốc của project
snyk trust .

# Trust thư mục download
snyk trust ./download

# Trust thư mục extract
snyk trust ./extract

# Trust tất cả thư mục chính
snyk trust .
snyk trust ./download
snyk trust ./extract
snyk trust ./docs
```

## 2. Các lệnh Snyk khác hữu ích

### 2.1. Snyk Authentication
```bash
# Đăng nhập vào Snyk
snyk auth

# Đăng xuất
snyk logout

# Kiểm tra version
snyk version
```

### 2.2. Snyk Code Scan (SAST)
Quét mã nguồn Python để tìm lỗ hổng bảo mật:

```bash
# Scan toàn bộ project
snyk code scan --path=.

# Scan thư mục download
snyk code scan --path=./download

# Scan với severity threshold
snyk code scan --path=. --severity-threshold=high

# Scan và bao gồm cả ignored vulnerabilities
snyk code scan --path=. --include-ignores
```

### 2.3. Snyk SCA Scan (Open Source Dependencies)
Quét các thư viện Python dependencies:

```bash
# Scan dependencies từ requirements.txt (nếu có)
snyk sca scan --path=. --command=python3

# Scan với package manager cụ thể
snyk sca scan --path=. --package-manager=pip --command=python3

# Scan và hiển thị dependency tree
snyk sca scan --path=. --print-deps --command=python3
```

### 2.4. Snyk Package Health Check
Kiểm tra sức khỏe của package trước khi sử dụng:

```bash
# Kiểm tra package Python
snyk package health check --package-name=requests --ecosystem=pypi

# Kiểm tra với version cụ thể
snyk package health check --package-name=requests --ecosystem=pypi --package-version=2.31.0
```

### 2.5. Snyk Send Feedback
Báo cáo số lượng lỗi đã sửa hoặc ngăn chặn:

```bash
# Báo cáo sau khi sửa lỗi
snyk send feedback --path=. --fixed-existing-issues-count=5 --prevented-issues-count=0

# Báo cáo sau khi ngăn chặn lỗi mới
snyk send feedback --path=. --fixed-existing-issues-count=0 --prevented-issues-count=3
```

## 3. Workflow đề xuất cho project này

### Bước 1: Trust và Authenticate
```bash
# Trust project folder
snyk trust .

# Đăng nhập Snyk (nếu chưa)
snyk auth
```

### Bước 2: Scan mã nguồn Python
```bash
# Scan toàn bộ mã nguồn
snyk code scan --path=.

# Hoặc scan từng module
snyk code scan --path=./download
```

### Bước 3: Scan dependencies
```bash
# Nếu có requirements.txt
snyk sca scan --path=. --command=python3
```

### Bước 4: Kiểm tra package trước khi cài đặt
```bash
# Ví dụ kiểm tra package mitmproxy
snyk package health check --package-name=mitmproxy --ecosystem=pypi
```

## 4. Script tự động hóa

Tạo file `snyk_scan_all.bat` để chạy tất cả các scan:

```batch
@echo off
echo ===== Snyk Security Scan =====
echo.

echo [1/4] Trusting project folder...
snyk trust .

echo.
echo [2/4] Authenticating...
snyk auth

echo.
echo [3/4] Scanning source code...
snyk code scan --path=. --severity-threshold=medium

echo.
echo [4/4] Scanning dependencies...
snyk sca scan --path=. --command=python3

echo.
echo ===== Scan Complete =====
pause
```

## 5. Lưu ý quan trọng

- **Trust command**: Chỉ trust các folder bạn tin tưởng, vì Snyk sẽ có quyền đọc mã nguồn
- **Path format**: Trên Windows, sử dụng absolute path hoặc relative path với dấu `/` hoặc `\`
- **Python command**: Đảm bảo `python3` hoặc `python` có trong PATH
- **Rate limiting**: Snyk có giới hạn số lần scan, nên sử dụng hợp lý

## 6. Tích hợp với Git Hooks

Có thể tạo pre-commit hook để tự động scan:

```bash
# .git/hooks/pre-commit
#!/bin/bash
snyk code scan --path=. --severity-threshold=high
if [ $? -ne 0 ]; then
    echo "Snyk scan failed! Please fix security issues before committing."
    exit 1
fi
```
