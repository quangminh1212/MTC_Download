"""Find specific target books by scanning all API pages."""
import requests, json
import urllib3; urllib3.disable_warnings()
import io, sys

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'https://android.lonoapp.net/api'
PROXY = {'https': 'http://127.0.0.1:8081'}
SESS = requests.Session()
SESS.verify = False

TARGET_KEYWORDS = [
    'Phế Vật', 'Diễn Hóa', 'Trường Sinh', 'Võ Thần Điện',
    'Tiên Thần Đạo', 'Quản Lý', 'Phế Vật Lớp', 'Môn Phái Võ Lâm'
]

all_books = []
found_targets = []

for page in range(1, 50):
    try:
        r = SESS.get(f'{BASE}/books', params={'page': page, 'per_page': 20}, timeout=15, proxies=PROXY)
        d = r.json()
        books = d.get('data', [])
        if not books:
            print(f'Page {page}: no more books, total={len(all_books)}')
            break
        all_books.extend(books)
        for b in books:
            name = b.get('name', '')
            for kw in TARGET_KEYWORDS:
                if kw in name:
                    found_targets.append(b)
                    print(f'FOUND TARGET: id={b["id"]} name={name}')
                    break
    except Exception as e:
        print(f'Page {page} error: {e}')
        break

print(f'\n=== TOTAL BOOKS: {len(all_books)} ===')
print(f'=== TARGET BOOKS FOUND: {len(found_targets)} ===')
for b in found_targets:
    print(f'  id={b["id"]} name={b["name"]}')
    
# Save all books to file for manual inspection
with open('all_books.json', 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=2)
print('\nSaved to all_books.json')
