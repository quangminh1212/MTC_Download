#!/usr/bin/env python3
"""Phân tích thủ công file encrypted."""
import base64
import json
from pathlib import Path

# Đọc file encrypted
sample_file = Path('extract/novels/Chiến Lược Gia Thiên Tài/Chương 1.txt')
with open(sample_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('=== PHÂN TÍCH FILE ===')
print(f'Số dòng: {len(lines)}')
print(f'Dòng 0 (title): {lines[0].strip()}')

# Lấy nội dung encrypted
encrypted = lines[2].strip() if len(lines) > 2 else ''
print(f'\n=== NỘI DUNG ENCRYPTED ===')
print(f'Độ dài: {len(encrypted)}')
print(f'100 ký tự đầu: {encrypted[:100]}')

# Decode base64
encrypted_clean = encrypted.replace('\n', '').replace('\r', '').replace(' ', '')
missing_padding = len(encrypted_clean) % 4
if missing_padding:
    encrypted_clean += '=' * (4 - missing_padding)

try:
    decoded = base64.b64decode(encrypted_clean)
    print(f'\n=== SAU KHI DECODE ===')
    print(f'Độ dài: {len(decoded)} bytes')
    
    # Hiển thị dưới dạng hex để xem cấu trúc
    print(f'50 bytes đầu (hex): {decoded[:50].hex()}')
    
    # Tìm vị trí của các key JSON
    iv_pos = decoded.find(b'"iv"')
    value_pos = decoded.find(b'"value"')
    mac_pos = decoded.find(b'"mac"')
    
    print(f'\nVị trí các key:')
    print(f'  "iv" tại: {iv_pos}')
    print(f'  "value" tại: {value_pos}')
    print(f'  "mac" tại: {mac_pos}')
    
    # Extract manually
    if iv_pos >= 0:
        # Tìm giá trị iv
        iv_start = decoded.find(b':"', iv_pos) + 2
        iv_end = decoded.find(b'"', iv_start)
        iv_b64 = decoded[iv_start:iv_end]
        print(f'\nIV (base64): {iv_b64}')
        try:
            iv = base64.b64decode(iv_b64)
            print(f'IV (hex, {len(iv)} bytes): {iv.hex()}')
        except:
            print('IV không decode được')
    
    if value_pos >= 0:
        # Tìm giá trị value
        value_start = decoded.find(b':"', value_pos) + 2
        value_end = decoded.find(b'"', value_start)
        value_b64 = decoded[value_start:value_end]
        print(f'\nValue (base64, {len(value_b64)} bytes): {value_b64[:50]}...')
        try:
            value = base64.b64decode(value_b64)
            print(f'Value (hex, {len(value)} bytes): {value[:32].hex()}...')
        except:
            print('Value không decode được')
    
    if mac_pos >= 0:
        # Tìm giá trị mac
        mac_start = decoded.find(b':"', mac_pos) + 2
        mac_end = decoded.find(b'"', mac_start)
        mac = decoded[mac_start:mac_end]
        print(f'\nMAC: {mac}')
        
except Exception as e:
    print(f'Lỗi: {e}')
    import traceback
    traceback.print_exc()
