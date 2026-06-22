#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys, time
from pathlib import Path
import requests

EMAIL = sys.argv[1]
PASSWORD = sys.argv[2]
BASE = 'https://android.lonoapp.net/api'
OUT = Path(r'C:\Dev\MTC_Download\logs')
OUT.mkdir(parents=True, exist_ok=True)

s = requests.Session()
s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json','Content-Type':'application/json'})
r = s.post(BASE + '/auth/login', json={'email':EMAIL,'password':PASSWORD,'device_name':'OpenClaw Windows'}, timeout=30)
print('login', r.status_code)
r.raise_for_status()
data = r.json()
if not data.get('success'):
    raise SystemExit(data)
token = data['data']['token']
s.headers.update({'Authorization': f'Bearer {token}'})

all_items=[]
seen=set()
page=1
while True:
    r=s.get(BASE + '/bookmarks', params={'page':page}, timeout=30)
    print('bookmarks page', page, r.status_code, r.url)
    r.raise_for_status()
    j=r.json()
    items=j.get('data') or []
    if not items:
        break
    for it in items:
        bid=it.get('book_id') or (it.get('book') or {}).get('id')
        key=(bid, it.get('chapter_id'))
        if key not in seen:
            seen.add(key)
            all_items.append(it)
    pagination=j.get('pagination') or {}
    current=pagination.get('current') or page
    last=pagination.get('last') or current
    if current >= last:
        break
    page += 1
    time.sleep(1)

books={}
for it in all_items:
    b=it.get('book') or {}
    bid=it.get('book_id') or b.get('id')
    if bid:
        books[str(bid)]={
            'id': bid,
            'name': b.get('name'),
            'slug': b.get('slug'),
            'latest_index': b.get('latest_index'),
            'link': b.get('link'),
            'bookmark_id': it.get('id'),
            'chapter_id': it.get('chapter_id'),
            'created_at': it.get('created_at')
        }
manifest={'count_bookmarks':len(all_items),'count_books':len(books),'books':list(books.values())}
path=OUT/'bookmarked_books_manifest.json'
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print('saved', path)
print('count_bookmarks', manifest['count_bookmarks'])
print('count_books', manifest['count_books'])
for b in manifest['books']:
    print(f"{b['id']}\t{b.get('latest_index')}\t{b.get('name')}")
