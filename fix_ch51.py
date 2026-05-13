from pathlib import Path
import re
p = Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du\Chương 51 Đóng sách!.txt')
s = p.read_text(encoding='utf-8', errors='replace')
# Keep title header, drop garbage before a sane Vietnamese opening.
markers = ['Chào các bạn đọc hiện tại', 'Chào các bạn đọc', 'Dạo gần đây mình cảm thấy']
idx = -1
for m in markers:
    i = s.find(m)
    if i != -1:
        idx = i
        break
if idx != -1:
    header = '============================================================\nChương 51: Đóng sách!\n============================================================\n\n'
    body = s[idx:].lstrip()
    p.write_text(header + body + ('\n' if not body.endswith('\n') else ''), encoding='utf-8')
    print('fixed_ch51')
else:
    print('marker_not_found')
