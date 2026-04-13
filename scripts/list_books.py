import urllib.request, json

base = 'https://android.lonoapp.net/api'
headers = {'User-Agent': 'Dart/2.19 (dart:io)'}

def get(path):
    req = urllib.request.Request(base + path, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

all_books = []
for page in range(1, 22):
    d = get('/books?page=' + str(page))
    books = d.get('data', [])
    if not books:
        break
    all_books.extend(books)

print("Total: " + str(len(all_books)))
for b in all_books:
    print(str(b['id']) + "  " + b['name'])
