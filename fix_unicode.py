#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def fix_unicode_in_file(filepath):
    """Sửa Unicode escape sequences trong file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Decode Unicode escape sequences
        try:
            # Sử dụng regex để tìm và thay thế Unicode escape sequences
            import codecs

            def decode_unicode_match(match):
                try:
                    return codecs.decode(match.group(0), 'unicode_escape')
                except:
                    return match.group(0)

            # Tìm tất cả Unicode escape sequences và decode chúng
            fixed_content = re.sub(r'\\u[0-9a-fA-F]{4}', decode_unicode_match, content)

        except Exception as e:
            print(f"Không thể decode {filepath}: {e}")
            return False
        
        # Loại bỏ các thẻ HTML còn sót lại
        fixed_content = re.sub(r'<a href=\\?[^>]*>', '', fixed_content)
        fixed_content = re.sub(r'</a>', '', fixed_content)
        
        # Lưu lại file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✓ Đã sửa: {filepath}")
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi sửa {filepath}: {e}")
        return False

def main():
    """Sửa tất cả file trong thư mục truyện"""
    story_folder = "Tận_Thế_Chi_Siêu_Thị_Hệ_Thống"
    
    if not os.path.exists(story_folder):
        print(f"Không tìm thấy thư mục: {story_folder}")
        return
    
    print(f"Đang sửa Unicode trong thư mục: {story_folder}")
    
    success = 0
    total = 0
    
    for filename in os.listdir(story_folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(story_folder, filename)
            total += 1
            if fix_unicode_in_file(filepath):
                success += 1
    
    print(f"\nHoàn thành! Đã sửa {success}/{total} file")

if __name__ == "__main__":
    main()
