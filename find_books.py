"""Find target book IDs via the API."""
import requests, json
import urllib3; urllib3.disable_warnings()

BASE = 'https://android.lonoapp.net/api'
PROXY = {'https': 'http://127.0.0.1:8081'}
SESS = requests.Session()
SESS.verify = False

# Get ALL books across many pages to find the ones we need
all_books = []
for page in range(1, 30):
    try:
        r = SESS.get(f'{BASE}/books', params={'page': page, 'per_page': 50}, timeout=15, proxies=PROXY)
        d = r.json()
        books = d.get('data', [])
        if not books:
            print(f'Page {page}: empty, stopping')
            break
        all_books.extend(books)
        print(f'Page {page}: {len(books)} books (total={len(all_books)})')
        # Print names to scan for Vietnamese content
        for b in books:
            name = b.get('name', '')
            if any(kw in name for kw in ['Quản', 'Tiên', 'Võ', 'Thần', 'Đạo', 'Vật', 'Tu', 'Linh', 'Thánh', 'Kiếm', 'Ma', 'Đế', 'Vương']):
                print(f'  ** VIETNAMESE: id={b["id"]} name={name[:80]}')
    except Exception as e:
        print(f'Page {page} error: {e}')
        break

# Search by specific keywords
keywords = ['Phế Vật', 'Diễn Hóa', 'Trường Sinh', 'Võ Thần', 'Tiên Thần', 'Lớp']
for kw in keywords:
    for endpoint in ['/books', '/books/search']:
        try:
            r = SESS.get(f'{BASE}{endpoint}', params={'keyword': kw, 'q': kw, 'search': kw}, timeout=10, proxies=PROXY)
            d = r.json()
            results = d.get('data', d if isinstance(d, list) else [])
            if results:
                print(f'KW [{kw}] via {endpoint}: {len(results)} results')
                for b in results[:3]:
                    print(f'  id={b.get("id")} name={b.get("name","?")}')
        except:
            pass

print(f'\nTotal books found: {len(all_books)}')

# Find specifically: target novels  
targets = ['Phế Vật', 'Diễn Hóa', 'Trường Sinh', 'Võ Thần Điện', 'Tiên Thần Đạo']
for b in all_books:
    name = b.get('name', '')
    for t in targets:
        if t in name:
            print(f'TARGET: id={b["id"]} name={name}')
            break
