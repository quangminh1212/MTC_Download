"""Find books in all_books.json matching our downloaded novels."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('all_books.json', encoding='utf-8') as f:
    books = json.load(f)

print(f'Total books: {len(books)}')

# Our download folder names
folder_names = [
    'Huyền Huyễn_ Nguyên Lai Ta Là Tuyệt Thế Võ Thần',
    'Ta Treo Máy Ngàn Vạn Năm',
    'Để Ngươi Người Quản Lý Phế Vật Lớp',
]

# Search keywords
keywords = ['Huyền Huyễn', 'Tuyệt Thế Võ Thần', 'Ta Treo Máy', 'Ngàn Vạn', 'Phế Vật Lớp']

for b in books:
    name = b.get('name', '')
    for kw in keywords:
        if kw in name:
            print(f'MATCH: id={b["id"]} name={name}')
            break

# Also try fuzzy match by first few chars
for folder in folder_names:
    first_word = folder.split()[0]
    matches = [b for b in books if first_word in b.get('name', '')]
    if matches:
        print(f'=== Folder: {folder[:40]} ===')
        for b in matches[:3]:
            print(f'  id={b["id"]} name={b["name"]}')
