#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import codecs

# Đọc file để debug
with open('Tận_Thế_Chi_Siêu_Thị_Hệ_Thống/Chương 1.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("Original content (first 200 chars):")
print(repr(content[:200]))

# Test decode
def decode_unicode_match(match):
    try:
        return codecs.decode(match.group(0), 'unicode_escape')
    except:
        return match.group(0)

# Tìm tất cả Unicode escape sequences và decode chúng
decoded_content = re.sub(r'\\u[0-9a-fA-F]{4}', decode_unicode_match, content)

print("\nDecoded content (first 200 chars):")
print(repr(decoded_content[:200]))

print("\nActual decoded text:")
print(decoded_content[:200])

# Lưu file đã decode
with open('Tận_Thế_Chi_Siêu_Thị_Hệ_Thống/Chương 1_decoded.txt', 'w', encoding='utf-8') as f:
    f.write(decoded_content)

print("\nĐã lưu file decoded: Chương 1_decoded.txt")
