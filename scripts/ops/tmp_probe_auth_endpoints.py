import requests, json, time, sys
TOKEN = sys.argv[1]
BASE = 'https://android.lonoapp.net/api'
headers = {
    'User-Agent': 'MTC/Android',
    'Accept': 'application/json',
    'Authorization': f'Bearer {TOKEN}',
}
paths = [
    ('GET','/me',None),
    ('GET','/user',None),
    ('GET','/users/me',None),
    ('GET','/profile',None),
    ('GET','/library',None),
    ('GET','/bookmarks',None),
    ('GET','/favorites',None),
    ('GET','/favourites',None),
    ('GET','/books/bookmarks',None),
    ('GET','/books/favorites',None),
    ('GET','/books/library',None),
    ('GET','/chapters/bookmarks',None),
    ('GET','/bookmarks/books',None),
    ('GET','/library/books',None),
    ('GET','/users/library',None),
    ('GET','/users/bookmarks',None),
]
for method, path, params in paths:
    url = BASE + path
    try:
        r = requests.request(method, url, headers=headers, params=params, timeout=20)
        print('===', method, path, r.status_code)
        print(r.text[:3000].replace('\n',' '))
    except Exception as e:
        print('===', method, path, 'ERR', e)
    time.sleep(1)
