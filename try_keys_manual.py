#!/usr/bin/env python3
"""Thử các key tìm được với dữ liệu đã phân tích."""
import base64
import json
import re
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Dữ liệu đã phân tích
iv_b64 = 'Ygajn,st\x0c\x95J0@\xa4\x1f{\x8fgxV5sqDvIf3mmMHJA=='
value_b64_start = 'bThDEndM8QGM15oUivB3vY8BjkD17JvW1Zf1mn0JQIUP5safE+'
mac_hex = '7f8246619cb3264e70a70897288f19919d6a8f9761fce3ae4414bf64bb4139c7'

# Đọc lại file để lấy đầy đủ value
sample_file = Path('extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt')
with open(sample_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
encrypted = lines[2].strip() if len(lines) > 2 else ''

# Decode
encrypted_clean = encrypted.replace('\n', '').replace('\r', '').replace(' ', '')
missing_padding = len(encrypted_clean) % 4
if missing_padding:
    encrypted_clean += '=' * (4 - missing_padding)

decoded = base64.b64decode(encrypted_clean)

# Extract components
iv_start = decoded.find(b':"', decoded.find(b'"iv"')) + 2
iv_end = decoded.find(b'"', iv_start)
iv_b64_raw = decoded[iv_start:iv_end]

value_start = decoded.find(b':"', decoded.find(b'"value"')) + 2
value_end = decoded.find(b'"', value_start)
value_b64_raw = decoded[value_start:value_end]

mac_start = decoded.find(b':"', decoded.find(b'"mac"')) + 2
mac_end = decoded.find(b'"', mac_start)
mac_raw = decoded[mac_start:mac_end]

# Decode IV và value
# IV có thể chứa ký tự không hợp lệ, cần xử lý
print("=== PHÂN TÍCH CHI TIẾT ===")
print(f"IV raw: {iv_b64_raw}")
print(f"Value raw length: {len(value_b64_raw)}")
print(f"MAC raw: {mac_raw}")

# Thử decode IV
try:
    # Thêm padding nếu cần
    iv_clean = iv_b64_raw.replace(b'\n', b'').replace(b'\r', b'')
    iv_padding = len(iv_clean) % 4
    if iv_padding:
        iv_clean += b'=' * (4 - iv_padding)
    iv = base64.b64decode(iv_clean)
    print(f"\nIV decoded: {len(iv)} bytes")
    print(f"IV hex: {iv.hex()}")
except Exception as e:
    print(f"Lỗi decode IV: {e}")
    # Thử decode với errors='ignore'
    iv_clean = iv_b64_raw.decode('utf-8', errors='ignore').encode()
    iv = base64.b64decode(iv_clean)
    print(f"IV decoded (với ignore): {len(iv)} bytes")
    print(f"IV hex: {iv.hex()}")

# Thử decode value
try:
    value_clean = value_b64_raw.replace(b'\n', b'').replace(b'\r', b'')
    value_padding = len(value_clean) % 4
    if value_padding:
        value_clean += b'=' * (4 - value_padding)
    value = base64.b64decode(value_clean)
    print(f"\nValue decoded: {len(value)} bytes")
    print(f"Value first 32 bytes hex: {value[:32].hex()}")
except Exception as e:
    print(f"Lỗi decode value: {e}")

# MAC
mac = mac_raw.decode('utf-8', errors='ignore')
print(f"\nMAC: {mac}")

# Bây giờ thử các key
print("\n=== THỬ CÁC KEY ===")

# Đọc các hex keys từ dart_snapshot_strings.txt
strings_file = Path("dart_snapshot_strings.txt")
with open(strings_file, 'r', encoding='utf-8') as f:
    content = f.read()

hex_pattern = re.compile(r'^[0-9a-fA-F]{64}$', re.MULTILINE)
hex_keys = hex_pattern.findall(content)

print(f"Tìm thấy {len(hex_keys)} hex keys (64 chars)")

# Thử mỗi key
tested = 0
for key_hex in hex_keys[:100]:  # Thử 100 key đầu
    tested += 1
    try:
        key = bytes.fromhex(key_hex)
        if len(key) != 32:
            continue
        
        # Thử giải mã
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(value), AES.block_size)
        
        # Kiểm tra xem có phải UTF-8 hợp lệ không
        text = decrypted.decode('utf-8')
        
        if len(text) > 100:
            print(f"\n✅ THÀNH CÔNG!")
            print(f"Key hex: {key_hex}")
            print(f"Nội dung (200 chars): {text[:200]}")
            
            # Lưu kết quả
            with open("decrypted_chapter.txt", 'w', encoding='utf-8') as f:
                f.write(text)
            print("Đã lưu vào decrypted_chapter.txt")
            
            with open("APP_KEY.txt", 'w') as f:
                f.write(f"base64:{base64.b64encode(key).decode()}")
            print("Đã lưu key vào APP_KEY.txt")
            
            break
    except Exception as e:
        pass

print(f"\nĐã thử {tested} keys")
