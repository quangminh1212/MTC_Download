import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
books = json.load(open('all_books.json', encoding='utf-8'))

# device large export files (decoded from the ls output)
device_exports = [
    'Một Thế Vô Hạn Thôn Phệ',
    'Ta Có Trăm Vạn Điểm Kỹ Năng',
    'Tận Thế Biên Giới',
    'Để Ngươi Người Quản Lý Phế Vật Lớp, Làm Sao Thành Võ Thần Điện',
]

print('=== Large device exports vs all_books.json ===')
for n in device_exports:
    bk = next((b for b in books if b['name'] == n), None)
    if bk:
        print(f'  YES: id={bk["id"]} ch={bk["chapter_count"]} {n}')
    else:
        print(f'  NO:  {n}')

# Also print all books with fuzzy match for "Một Thế" or "Tận Thế"
print()
print('=== Fuzzy search in all_books.json ===')
for b in books:
    n = b['name']
    if any(kw in n for kw in ['Một Thế', 'Tận Thế', 'Thôn Phệ', 'Biên Giới']):
        print(f'  id={b["id"]} ch={b["chapter_count"]} {n}')
