import json
import requests
from pathlib import Path

cid = 15426215
book_id = 110512
bases = [
    'https://android.lonoapp.net/api',
    'https://api.lonoapp.net/api',
    'https://lonoapp.net/api',
    'https://vtruyen.com/api',
]
paths = [
    f'/chapters/{cid}',
    f'/chapters/{cid}/content',
    f'/chapters/{cid}/read',
    f'/chapters/{cid}/download',
    f'/chapter/{cid}',
    f'/chapter/{cid}/content',
    '/chapter_detail',
    f'/chapter_detail/{cid}',
    '/contents',
    f'/contents/{cid}',
    '/reader',
    '/read',
    '/download_chapter',
    '/offline_chapter',
]
paramsets = [
    {},
    {'id': cid},
    {'chapter_id': cid},
    {'book_id': book_id, 'chapter_id': cid},
    {'filter[chapter_id]': cid},
    {'include': 'book,creator,previous,next'},
    {'include': 'user,chapter'},
    {'full': 1},
    {'offline': 1},
    {'type': 'offline'},
]
headersets = [
    {'User-Agent':'MTC/Android','Accept':'application/json'},
    {'User-Agent':'okhttp/4.9.2','Accept':'application/json'},
    {'User-Agent':'Dart/3.0 (dart:io)','Accept':'application/json'},
]

out=[]
for base in bases:
  for path in paths:
    for params in paramsets:
      if path.endswith(str(cid)) and params not in ({}, {'include':'book,creator,previous,next'}, {'include':'user,chapter'}, {'full':1}, {'offline':1}, {'type':'offline'}):
        continue
      for headers in headersets:
        url=base+path
        try:
          r=requests.get(url,params=params,headers=headers,timeout=12)
          txt=r.text
          item={
            'status':r.status_code,
            'url':r.url,
            'ua':headers['User-Agent'],
            'ctype':r.headers.get('content-type'),
            'len':len(txt),
            'head':txt[:260].replace('\n',' '),
          }
          if r.status_code == 200 and len(txt)>100:
            out.append(item)
            print(r.status_code, len(txt), r.url)
        except Exception as e:
          pass
Path(r'C:\Dev\MTC_Download\logs\probe_locked_chapter_endpoints.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('saved', len(out))
